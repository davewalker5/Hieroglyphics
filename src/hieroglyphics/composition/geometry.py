"""Pack sign ink bounds for both scoring and rendering."""

from dataclasses import dataclass
from itertools import accumulate

from hieroglyphics.composition.configuration import DEFAULT_SETTINGS, QUADRAT_SIZE, Constraints
from hieroglyphics.composition.quadrat import Axis, Group, Node
from hieroglyphics.composition.sign_layout import sign_layout


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
    constraints: Constraints

    @property
    def scale(self) -> float:
        """
        Fit the drawing within a quadrat while retaining its proportions.

        :return: Uniform scale in the range (0, 1].
        """
        width_limit = QUADRAT_SIZE
        if not self.constraints.variable_width:
            width_limit = min(QUADRAT_SIZE, QUADRAT_SIZE * self.constraints.target_aspect_ratio)
        return min(1, width_limit / self.width, QUADRAT_SIZE / self.height)

    @property
    def viewport_width(self) -> float:
        """
        Compute a snug viewport width after scaling.

        :return: Width in design units.
        """
        if self.constraints.variable_width:
            return self.width * self.scale
        return min(QUADRAT_SIZE, QUADRAT_SIZE * self.constraints.target_aspect_ratio)

    @property
    def spaced_width(self) -> float:
        """
        Allocate half the minimum inter-quadrat gap on each side.

        :return: Width in design units, including the shared clearance.
        """
        return self.viewport_width + self.constraints.minimum_quadrat_gap

    @property
    def left_padding(self) -> float:
        """
        Centre the drawing in its viewport.

        :return: Space to the left in design units.
        """
        return (self.spaced_width - self.width * self.scale) / 2

    @property
    def top_padding(self) -> float:
        """
        Centre the drawing vertically in its common-height viewport.

        :return: Space above the drawing in design units.
        """
        return (QUADRAT_SIZE - self.height * self.scale) / 2


def draw_quadrat(
    node: Node, constraints: Constraints = DEFAULT_SETTINGS.constraints
) -> QuadratDrawing:
    """
    Pack a node's ink bounds, centring children across the grouping axis.

    :param node: Sign or group to lay out.
    :param constraints: Spacing and viewport configuration.
    :return: Drawing measured from its upper-left ink corner, with y increasing down.
    """
    if not isinstance(node, Group):
        layout = sign_layout(node.glyph)
        return QuadratDrawing(
            layout.width, layout.height,
            (PlacedSign(node.glyph, -layout.left, layout.top),), constraints,
        )

    children = tuple(draw_quadrat(child, constraints) for child in node.children)
    horizontal = node.axis is Axis.HORIZONTAL
    lengths = [child.width if horizontal else child.height for child in children]
    breadth = max(child.height if horizontal else child.width for child in children)
    length = sum(lengths) + constraints.sign_gap * (len(children) - 1)

    signs: list[PlacedSign] = []
    offsets = accumulate((size + constraints.sign_gap for size in lengths), initial=0)
    for child, offset in zip(children, offsets):
        if horizontal:
            x, y = offset, (breadth - child.height) / 2
        else:
            x, y = (breadth - child.width) / 2, offset
        signs.extend(PlacedSign(sign.glyph, sign.x + x, sign.y + y) for sign in child.signs)

    width, height = (length, breadth) if horizontal else (breadth, length)
    return QuadratDrawing(width, height, tuple(signs), constraints)
