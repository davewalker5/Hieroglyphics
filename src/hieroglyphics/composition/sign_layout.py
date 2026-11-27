"""Spatial metadata for the glyphs used in the transliteration alphabet."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class Proportion(Enum):
    """Broad visual categories used by automatic composition."""

    TALL = "tall"
    WIDE = "wide"
    COMPACT = "compact"
    LARGE = "large"


@dataclass(frozen=True)
class SignLayout:
    """Proportion and ink bounds in the bundled Noto font's design units."""

    proportion: Proportion
    width: int
    height: int
    top: int
    left: int = 49


TALL = Proportion.TALL
WIDE = Proportion.WIDE
COMPACT = Proportion.COMPACT
LARGE = Proportion.LARGE

# The Unicode sign is also the catalogue key. Store only spatial data here.
# Bounds come from the bundled font's glyph outlines (1,000 units per em).
_LAYOUTS = MappingProxyType({
    "𓄿": SignLayout(LARGE, 888, 996, 996),
    "𓃀": SignLayout(TALL, 800, 1294, 1001),
    "𓋴": SignLayout(TALL, 320, 1256, 1012),
    "𓂧": SignLayout(WIDE, 1476, 525, 603),
    "𓇋": SignLayout(TALL, 244, 1001, 1001),
    "𓆑": SignLayout(WIDE, 1408, 394, 383, left=47),
    "𓎼": SignLayout(COMPACT, 500, 439, 680),
    "𓉔": SignLayout(LARGE, 1023, 867, 846),
    "𓆓": SignLayout(LARGE, 972, 1012, 1002),
    "𓎡": SignLayout(WIDE, 981, 282, 551),
    "𓃭": SignLayout(WIDE, 1262, 511, 507),
    "𓅓": SignLayout(LARGE, 1018, 1019, 1001),
    "𓈖": SignLayout(WIDE, 1099, 196, 115),
    "𓍯": SignLayout(LARGE, 1035, 1019, 1000),
    "𓊪": SignLayout(COMPACT, 305, 369, 345),
    "𓈎": SignLayout(COMPACT, 624, 606, 528),
    "𓂋": SignLayout(WIDE, 1079, 286, 281),
    "𓏏": SignLayout(COMPACT, 535, 264, 466),
    "𓅱": SignLayout(LARGE, 762, 1015, 1002),
    "𓇌": SignLayout(TALL, 556, 1001, 1001),
    "𓊃": SignLayout(WIDE, 1259, 183, 146),
})
_DEFAULT_LAYOUT = SignLayout(LARGE, 1500, 1650, 1324, left=0)


def sign_layout(glyph: str) -> SignLayout:
    """
    Look up a sign's visual properties.

    :param glyph: Unicode character identifying the sign.
    :return: Sign layout, with a conservative standalone box for unknown signs.
    """
    return _LAYOUTS.get(glyph, _DEFAULT_LAYOUT)
