"""Load, search and regenerate the packaged sign catalogue."""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
from unicodedata import normalize

from hieroglyphics.transliteration import load_transliterations
from hieroglyphics.transliteration.unikemet import load_unikemet, validate_correspondences

DATA_DIRECTORY = Path(__file__).parent / "data"
_GARDINER_GROUPS = {
    "D": "Parts of the human body",
    "E": "Mammals",
    "G": "Birds",
    "I": "Amphibians and reptiles",
    "M": "Trees and plants",
    "N": "Sky, earth and water",
    "O": "Buildings and parts of buildings",
    "Q": "Domestic and funerary furniture",
    "S": "Crowns, dress and equipment",
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
        return re.sub(r"^([A-Z]+)0+(?=\d)", r"\1", identifier)

    @property
    def group(self) -> str:
        """Return the initial classification group for browsing."""
        return self.properties.get("kEH_Cat", "").partition("-")[0]

    @property
    def description(self) -> str:
        """Return the depiction documented by UniKemet."""
        return self.properties.get("kEH_Desc", "").strip()

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
    data = json.loads((DATA_DIRECTORY / "signs.json").read_text(encoding="utf-8"))
    signs = {int(scalar, 16): Sign(int(scalar, 16), MappingProxyType(properties))
             for scalar, properties in data["signs"].items()}
    return data["unicode_version"], MappingProxyType(signs)


def group_label(group: str) -> str:
    """
    Return a readable name for the classification group.

    :param group: Group prefix from the UniKemet catalogue classification.
    :return: The group code and its label where known.
    """
    return f"{group} · {_GARDINER_GROUPS[group]}" if group in _GARDINER_GROUPS else group


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


def generate_catalogue(project_root: Path) -> None:
    """
    Regenerate the packaged subset from the pinned source and the shipped table.

    :param project_root: Checkout containing the source data and application.
    :raises ValueError: If the source checksum differs or a correspondence cannot be resolved.
    """
    source = project_root / "data"
    provenance = json.loads((source / "Unikemet-provenance.json").read_text(encoding="utf-8"))
    snapshot = source / "Unikemet.txt"
    if sha256(snapshot.read_bytes()).hexdigest() != provenance["sha256"]:
        raise ValueError("UniKemet snapshot differs from its pinned SHA-256 checksum")

    table_path = project_root / "src/hieroglyphics/transliteration/data/alphabet_l_to_r.csv"
    # An absolute path bypasses the optional runtime correspondence directory.
    correspondences = load_transliterations(str(table_path.resolve()))
    signs = load_unikemet(snapshot)
    validate_correspondences(correspondences, signs)
    scalars = sorted({ord(glyph) for sequence in correspondences.values() for glyph in sequence})
    data = {**provenance, "signs": {f"{scalar:05X}": signs[scalar] for scalar in scalars}}
    destination = project_root / "src/hieroglyphics/catalogue/data"
    (destination / "signs.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / provenance["license_file"]).write_bytes((source / provenance["license_file"]).read_bytes())


if __name__ == "__main__":
    generate_catalogue(Path(__file__).resolve().parents[3])
