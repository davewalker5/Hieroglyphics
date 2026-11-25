"""
Offline validation of transliterator correspondences against UniKemet
"""

import re
from collections.abc import Mapping
from pathlib import Path

_CODE_POINT = re.compile(r"U\+([0-9A-F]{4,6})")
_PROPERTY = re.compile(r"kEH_[A-Za-z0-9]+")


def load_unikemet(path: Path) -> dict[int, dict[str, str]]:
    """
    Read the UniKemet properties grouped by Unicode scalar.

    :param path: Path to the original UTF-8 UniKemet data file.
    :return: The raw property values for each scalar.
    :raises ValueError: If the file is empty or a record is malformed or duplicated.
    """
    signs: dict[int, dict[str, str]] = {}
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            record = line.rstrip("\n")
            if not record.strip() or record.startswith("#"):
                continue

            fields = record.split("\t")
            if len(fields) != 3:
                raise ValueError(f"{path}:{line_number}: expected three tab-separated fields")

            code_point, property_name, value = fields
            match = _CODE_POINT.fullmatch(code_point)
            if match is None or not _PROPERTY.fullmatch(property_name) or not value.strip():
                raise ValueError(f"{path}:{line_number}: invalid UniKemet record")

            scalar = int(match[1], 16)
            if scalar > 0x10FFFF or 0xD800 <= scalar <= 0xDFFF:
                raise ValueError(f"{path}:{line_number}: invalid Unicode scalar {code_point}")

            properties = signs.setdefault(scalar, {})
            if property_name in properties:
                raise ValueError(f"{path}:{line_number}: duplicate {property_name} for {code_point}")
            properties[property_name] = value

    if not signs:
        raise ValueError(f"{path}: no UniKemet records found")

    return signs


def validate_correspondences(
    correspondences: Mapping[str, str],
    signs: Mapping[int, Mapping[str, str]],
) -> None:
    """
    Verify that every sign occurrence in the correspondence table has a UniKemet record.

    :param correspondences: Input letters mapped to ordered strings of signs.
    :param signs: UniKemet properties indexed by Unicode scalar.
    :raises ValueError: If any input letter emits a scalar absent from UniKemet.
    """
    missing = [
        f"{letter!r} position {position}: U+{ord(glyph):04X}"
        for letter, sequence in correspondences.items()
        for position, glyph in enumerate(sequence, start=1)
        if ord(glyph) not in signs
    ]
    if missing:
        raise ValueError("Missing UniKemet records: " + ", ".join(missing))
