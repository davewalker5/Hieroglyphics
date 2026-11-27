"""Lay out quadrats for the shared SVG template."""

from dataclasses import dataclass
from itertools import accumulate

from hieroglyphics.composition.quadrat import Axis, Composition, Group, Node
from hieroglyphics.composition.sign_layout import sign_layout

SIGN_GAP = 70  # Font design units between ink bounds.
QUADRAT_SIZE = 1650  # Maximum width and common height in design units.


@dataclass(frozen=True)
class PlacedSign:
    """A glyph and the position of its alphabetic baseline origin."""

    glyph: str
    x: float
    y: float


@dataclass(frozen=True)
class QuadratDrawing:
    """A quadrat's dimensions and glyph positions in logical order."""

    width: int
    height: int
    signs: tuple[PlacedSign, ...]

    @property
    def scale(self) -> float:
        """
        Fit the drawing within a quadrat while retaining its proportions.

        :return: Uniform scale in the range (0, 1].
        """
        return min(1, QUADRAT_SIZE / max(self.width, self.height))

    @property
    def viewport_width(self) -> float:
        """
        Compute a snug viewport width after scaling.

        :return: Width in design units.
        """
        return self.width * self.scale

    @property
    def top_padding(self) -> float:
        """
        Centre the drawing vertically in its common-height viewport.

        :return: Space above the drawing in design units.
        """
        return (QUADRAT_SIZE - self.height * self.scale) / 2


def _draw(node: Node) -> QuadratDrawing:
    """
    Pack a node's ink bounds, centring children across the grouping axis.

    :param node: Sign or group to lay out.
    :return: Drawing measured from its upper-left ink corner, with y increasing down.
    """
    if not isinstance(node, Group):
        layout = sign_layout(node.glyph)
        return QuadratDrawing(
            layout.width, layout.height,
            (PlacedSign(node.glyph, -layout.left, layout.top),),
        )

    children = tuple(_draw(child) for child in node.children)
    horizontal = node.axis is Axis.HORIZONTAL
    lengths = [child.width if horizontal else child.height for child in children]
    breadth = max(child.height if horizontal else child.width for child in children)
    length = sum(lengths) + SIGN_GAP * (len(children) - 1)

    signs: list[PlacedSign] = []
    offsets = accumulate((size + SIGN_GAP for size in lengths), initial=0)
    for child, offset in zip(children, offsets):
        if horizontal:
            x, y = offset, (breadth - child.height) / 2
        else:
            x, y = (breadth - child.width) / 2, offset
        signs.extend(PlacedSign(sign.glyph, sign.x + x, sign.y + y) for sign in child.signs)

    width, height = (length, breadth) if horizontal else (breadth, length)
    return QuadratDrawing(width, height, tuple(signs))


def render_quadrats(composition: Composition) -> tuple[tuple[QuadratDrawing, ...], ...]:
    """
    Prepare SVG drawings while preserving word boundaries and reading order.

    :param composition: Ordered words and quadrats.
    :return: Per-word drawings with direction-independent geometry.
    """
    return tuple(tuple(_draw(node) for node in word) for word in composition.words)
