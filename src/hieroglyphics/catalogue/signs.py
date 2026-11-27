"""Load, search and regenerate the packaged sign catalogue."""

import argparse
import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Mapping, TypedDict
from unicodedata import normalize

from hieroglyphics.transliteration import load_transliterations
from hieroglyphics.transliteration.unikemet import load_unikemet, validate_correspondences

DATA_DIRECTORY = Path(__file__).parent / "data"
_CATALOGUE_PATH = DATA_DIRECTORY / "signs.json"
_TRANSLITERATION_PATH = (
    Path(__file__).resolve().parents[1] / "transliteration/data/alphabet_l_to_r.csv"
)
_GARDINER_PADDING = re.compile(r"^([A-Z]+)0+(?=\d)")
_SNAPSHOT_HEADER = re.compile(r"# Unikemet-(\d+\.\d+\.\d+)\.txt")
_LICENCE_NAME = "Unikemet-LICENSE.txt"
_LOGGER = logging.getLogger(__name__)
_GARDINER_GROUPS = {
    "A": "Men and their occupations",
    "B": "Women and their occupations",
    "D": "Parts of the human body",
    "E": "Mammals",
    "F": "Parts of mammals",
    "G": "Birds",
    "I": "Amphibians and reptiles",
    "L": "Invertebrates and lesser animals",
    "M": "Trees and plants",
    "N": "Sky, earth and water",
    "O": "Buildings and parts of buildings",
    "P": "Ships and parts of ships",
    "Q": "Domestic and funerary furniture",
    "S": "Crowns, dress and equipment",
    "U": "Agriculture, crafts and professions",
    "V": "Rope, fibre and baskets",
    "W": "Vessels",
    "X": "Bread and cakes",
}
_PLAIN_CONSONANTS = re.compile(r"[ꜣꞽyꜥwbpfmnrhḥḫẖsšḳkgtṯdḏ]{1,3}")


@dataclass(frozen=True)
class Sign:
    """A Unicode scalar and its original UniKemet properties."""

    scalar: int
    properties: Mapping[str, str]

    @property
    def code_point(self) -> str:
        """Return the standard hexadecimal notation for the sign."""
        return f"U+{self.scalar:05X}"

    @property
    def glyph(self) -> str:
        """Return the sign as Unicode text."""
        return chr(self.scalar)

    @property
    def gardiner(self) -> str:
        """Return the unpadded Gardiner label for an original-block sign."""
        identifier = self.properties.get("kEH_UniK", "")
        if not 0x13000 <= self.scalar <= 0x1342F:
            return ""
        return _GARDINER_PADDING.sub(r"\1", identifier)

    @property
    def group(self) -> str:
        """Return the initial classification group for browsing."""
        return self.properties.get("kEH_Cat", "").partition("-")[0]

    @property
    def description(self) -> str:
        """Return the depiction documented by UniKemet."""
        return self.properties.get("kEH_Desc", "").strip()

    @property
    def plain_phonetic_values(self) -> tuple[str, ...]:
        """
        Return documented readings when every alternative is unqualified.

        :return: Distinct NFC readings in catalogue order, or an empty tuple
            when any reading is missing, uncertain or its phonogram use is ambiguous.
        """
        function = self.properties.get("kEH_Func", "Phonemogram")
        if function.casefold() != "phonemogram":
            return ()
        raw_values = normalize("NFC", self.properties.get("kEH_FVal", ""))
        values = tuple(value.strip() for value in raw_values.split("|"))
        if not all(_PLAIN_CONSONANTS.fullmatch(value) for value in values):
            return ()
        return tuple(dict.fromkeys(values))

    @property
    def consonant_count(self) -> int | None:
        """Count consonants when a phonemogram has one plain, unqualified reading."""
        value = normalize("NFC", self.properties.get("kEH_FVal", ""))
        if self.properties.get("kEH_Func", "").casefold() == "phonemogram" and _PLAIN_CONSONANTS.fullmatch(value):
            return len(value)
        return None


@lru_cache(maxsize=1)
def get_catalogue() -> tuple[str, Mapping[int, Sign]]:
    """Return the pinned Unicode version and read-only sign index."""
    data = _catalogue_data()
    signs = {int(scalar, 16): Sign(int(scalar, 16), MappingProxyType(properties))
             for scalar, properties in data["signs"].items()}
    return data["unicode_version"], MappingProxyType(signs)


class _CatalogueData(TypedDict):
    """Runtime fields in the packaged catalogue JSON."""

    unicode_version: str
    licence: str
    signs: dict[str, dict[str, str]]


@lru_cache(maxsize=1)
def _catalogue_data() -> _CatalogueData:
    """
    Read the packaged catalogue, including its source metadata.

    :return: Catalogue data as loaded from JSON.
    """
    return json.loads(_CATALOGUE_PATH.read_text(encoding="utf-8"))


def get_catalogue_licence() -> str:
    """
    Return the Unicode notice embedded in the packaged catalogue.

    :return: Licence text for the catalogue records.
    """
    return _catalogue_data()["licence"]


def gardiner_group_name(group: str) -> str | None:
    """
    Look up the descriptive name of a Gardiner group.

    :param group: Classification group code.
    :return: Group name, if documented in the catalogue.
    """
    return _GARDINER_GROUPS.get(group)


def group_label(group: str) -> str:
    """
    Return a readable name for the classification group.

    :param group: Group prefix from the UniKemet catalogue classification.
    :return: The group code and its label where known.
    """
    name = gardiner_group_name(group)
    return f"{group} · {name}" if name else group


def search_signs(query: str, group: str, function: str, consonants: str) -> list[Sign]:
    """
    Find signs matching the query and all selected facets.

    :param query: Unicode notation, glyph, identifier, depiction or documented value.
    :param group: Optional UniKemet classification group.
    :param function: Optional source function label.
    :param consonants: Optional number of consonants for an unambiguous phonemogram.
    :return: Matching signs in code-point order.
    """
    term = normalize("NFC", query.strip()).casefold()
    description_query = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)") if term else None
    results = []
    for sign in get_catalogue()[1].values():
        if group and sign.group != group:
            continue
        if function and normalize("NFC", sign.properties.get("kEH_Func", "")) != function:
            continue
        if consonants and str(sign.consonant_count or "") != consonants:
            continue

        identifiers = [sign.code_point, sign.code_point[2:], sign.glyph, sign.gardiner]
        for property_name in ("kEH_UniK", "kEH_Cat", "kEH_HG", "kEH_JSesh"):
            identifiers.extend(sign.properties.get(property_name, "").split())
        values = sign.properties.get("kEH_FVal", "").split("|")
        searchable = {normalize("NFC", value.strip()).casefold() for value in identifiers + values}
        depiction = normalize("NFC", sign.description).casefold()
        if not term or term in searchable or (description_query and description_query.search(depiction)):
            results.append(sign)

    return results


def _select_signs(
    content_path: Path, records: Mapping[int, Mapping[str, str]]
) -> dict[int, Sign]:
    """
    Resolve the Gardiner codes in the selection against the snapshot.

    :param content_path: File with one Gardiner identifier per line.
    :param records: UniKemet properties indexed by Unicode scalar.
    :return: Requested signs indexed by Unicode scalar.
    :raises ValueError: If a code is unknown, ambiguous or duplicated.
    """
    signs_by_code: dict[str, list[Sign]] = {}
    for scalar, properties in records.items():
        sign = Sign(scalar, properties)
        if sign.gardiner:
            signs_by_code.setdefault(sign.gardiner, []).append(sign)

    selected: dict[int, Sign] = {}
    for line_number, line in enumerate(
        content_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        entry = line.partition("#")[0].strip().upper()
        if not entry:
            continue
        code = _GARDINER_PADDING.sub(r"\1", entry)
        matches = signs_by_code.get(code, [])
        if len(matches) != 1:
            reason = "Unknown" if not matches else "Ambiguous"
            raise ValueError(
                f"{content_path}:{line_number}: {reason} Gardiner code {entry}"
            )
        sign = matches[0]
        if sign.scalar in selected:
            raise ValueError(
                f"{content_path}:{line_number}: Duplicate Gardiner code {entry}"
            )
        _LOGGER.info("Selected %s (%s)", sign.gardiner, sign.code_point)
        selected[sign.scalar] = sign
    return selected


def _snapshot_metadata(snapshot_path: Path) -> dict[str, str]:
    """
    Read provenance and the notice accompanying the requested UniKemet snapshot.

    :param snapshot_path: UniKemet text file.
    :return: Snapshot metadata with the full licence text.
    :raises ValueError: If the checksum differs or the version is unavailable.
    """
    provenance_path = snapshot_path.with_name("Unikemet-provenance.json")
    checksum = sha256(snapshot_path.read_bytes()).hexdigest()
    if provenance_path.is_file():
        metadata = json.loads(provenance_path.read_text(encoding="utf-8"))
        if checksum != metadata["sha256"]:
            raise ValueError("UniKemet snapshot differs from its pinned SHA-256 checksum")
    else:
        with snapshot_path.open(encoding="utf-8") as snapshot:
            match = _SNAPSHOT_HEADER.fullmatch(snapshot.readline().strip())
        if match is None:
            raise ValueError(f"{snapshot_path}: UniKemet version missing from header")
        version = match[1]
        metadata = {
            "unicode_version": version,
            "source_url": f"https://www.unicode.org/Public/{version}/ucd/Unikemet.txt",
            "sha256": checksum,
        }

    licence_name = metadata.pop("license_file", _LICENCE_NAME)
    metadata["licence"] = snapshot_path.with_name(licence_name).read_text(encoding="utf-8")
    return metadata


def generate_catalogue(
    content_path: Path, snapshot_path: Path, output_path: Path = _CATALOGUE_PATH
) -> None:
    """
    Generate the catalogue from an explicit Gardiner selection and snapshot.

    :param content_path: Gardiner identifiers to transfer.
    :param snapshot_path: UniKemet snapshot with an adjacent Unicode licence.
    :param output_path: Location for the generated signs.json.
    :raises ValueError: If the input is invalid or required signs are missing.
    """
    metadata = _snapshot_metadata(snapshot_path)
    records = load_unikemet(snapshot_path)
    selected = _select_signs(content_path, records)
    # Use the shipped table even when the runtime has a custom table configured.
    correspondences = load_transliterations(str(_TRANSLITERATION_PATH))
    validate_correspondences(correspondences, records)
    missing = [
        f"{sign.gardiner} ({sign.code_point}, letter {letter}, position {position})"
        for letter, sequence in correspondences.items()
        for position, glyph in enumerate(sequence, start=1)
        if (sign := Sign(ord(glyph), records[ord(glyph)])).scalar not in selected
    ]
    if missing:
        raise ValueError(
            "Catalogue selection is missing required signs: " + ", ".join(missing)
        )

    entries: dict[str, Mapping[str, str]] = {}
    for sign in sorted(selected.values(), key=lambda sign: sign.scalar):
        entries[sign.code_point[2:]] = sign.properties
        _LOGGER.info("Transferring %s (%s)", sign.gardiner, sign.code_point)
    data = {**metadata, "signs": entries}
    contents = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with TemporaryDirectory(dir=output_path.parent) as temporary_directory:
        temporary_output = Path(temporary_directory) / output_path.name
        temporary_output.write_text(contents, encoding="utf-8")
        temporary_output.replace(output_path)
    _LOGGER.info("Wrote %d signs to %s", len(entries), output_path)


def _main() -> None:
    """Parse catalogue generation arguments and report failures on the command line."""
    parser = argparse.ArgumentParser(description="Regenerate the packaged sign catalogue.")
    parser.add_argument("content", type=Path, help="Gardiner identifier selection file")
    parser.add_argument("snapshot", type=Path, help="UniKemet snapshot file")
    parser.add_argument("--output", type=Path, default=_CATALOGUE_PATH, help="Output JSON path")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        generate_catalogue(arguments.content, arguments.snapshot, arguments.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    _main()
