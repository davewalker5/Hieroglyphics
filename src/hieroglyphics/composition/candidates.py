"""Generate and validate consecutive, order-preserving arrangements."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache

from hieroglyphics.composition.configuration import Constraints
from hieroglyphics.composition.geometry import QuadratDrawing, draw_quadrat
from hieroglyphics.composition.quadrat import Axis, Group, Node, Sign
from hieroglyphics.composition.sign_layout import has_layout, sign_layout


@dataclass(frozen=True)
class Candidate:
    """An arrangement with measured geometry and any reason for rejection."""

    node: Node
    drawing: QuadratDrawing
    rejection: str | None


def _validate_geometry(drawing: QuadratDrawing) -> str | None:
    """
    Check the physical constraints of a packed drawing.

    :param drawing: Arrangement measured by the shared, non-overlapping packer.
    :return: First rejection reason, or None. Single signs are always available.
    """
    if len(drawing.signs) == 1:
        return None
    constraints = drawing.constraints
    layouts = [sign_layout(sign.glyph) for sign in drawing.signs]
    if any(not has_layout(sign.glyph) for sign in drawing.signs):
        return "Unknown sign dimensions"
    if drawing.scale < 1 - constraints.maximum_reduction:
        return "Excessive uniform scaling"
    if any(max(layout.width, layout.height) * drawing.scale < constraints.minimum_rendered_extent
           for layout in layouts):
        return "Rendered sign extent below minimum"
    ratio = drawing.width / drawing.height
    if not constraints.minimum_aspect_ratio <= ratio <= constraints.maximum_aspect_ratio:
        return "Aspect ratio outside allowed range"
    if constraints.sign_gap * drawing.scale < constraints.minimum_sign_gap:
        return "Scaled gap below minimum"
    return None


def _validate_group(node: Node, depth: int, constraints: Constraints) -> str | None:
    """
    Validate each group against the configured depth and axis limits.

    :param node: Arrangement to validate.
    :param depth: Available grouping depth.
    :param constraints: Grouping limits.
    :return: First structural rejection reason, or None.
    """
    if isinstance(node, Sign):
        return None
    if depth == 0:
        return "Grouping depth exceeds maximum"
    limit = (
        constraints.maximum_horizontal if node.axis is Axis.HORIZONTAL
        else constraints.maximum_vertical
    )
    if len(node.children) > limit:
        return "Group width or stack exceeds maximum"
    for child in node.children:
        reason = _validate_group(child, depth - 1, constraints)
        if reason:
            return reason
    return None


def evaluate_arrangement(node: Node, constraints: Constraints) -> Candidate:
    """
    Measure and validate a manually or automatically created arrangement.

    :param node: Signs and groups in logical order.
    :param constraints: Grouping and geometry limits.
    :return: Drawing and first rejection reason, if any.
    """
    drawing = draw_quadrat(node, constraints)
    size = len(drawing.signs)
    reason = _validate_group(node, constraints.maximum_depth, constraints)
    if size != 1 and not constraints.minimum_signs <= size <= constraints.maximum_signs:
        reason = "Sign count outside allowed range"
    if any(sign.glyph.isspace() for sign in drawing.signs):
        reason = "Word separator inside quadrat"
    return Candidate(node, drawing, reason or _validate_geometry(drawing))


@lru_cache(maxsize=512)
def _arrangements(
    glyphs: str, depth: int, constraints: Constraints, axis: Axis | None = None
) -> tuple[Node, ...]:
    """
    Generate contiguous trees, flattening groups that share an axis.

    :param glyphs: Consecutive signs to arrange.
    :param depth: Remaining allowed grouping depth.
    :param constraints: Grouping limits.
    :param axis: Parent axis, excluded to avoid equivalent unflattened trees.
    :return: Trees in deterministic enumeration order.
    """
    if len(glyphs) == 1:
        return (Sign(glyphs),)
    if depth == 0:
        return ()

    limits = ((Axis.HORIZONTAL, constraints.maximum_horizontal),
              (Axis.VERTICAL, constraints.maximum_vertical))
    return tuple(
        Group(direction, children)
        for direction, limit in limits if direction is not axis
        for children in _child_groups(glyphs, depth - 1, constraints, direction, limit)
        if len(children) >= 2
    )


def _child_groups(
    glyphs: str, depth: int, constraints: Constraints, axis: Axis, slots: int
) -> Iterator[tuple[Node, ...]]:
    """
    Partition a group into consecutive children.

    :param glyphs: Remaining signs.
    :param depth: Available depth for each child.
    :param constraints: Grouping limits.
    :param axis: Parent axis.
    :param slots: Maximum remaining child count.
    :return: Possible ordered child tuples.
    """
    if not glyphs:
        yield ()
    elif slots:
        for size in range(1, len(glyphs) + 1):
            for child in _arrangements(glyphs[:size], depth, constraints, axis):
                for tail in _child_groups(glyphs[size:], depth, constraints, axis, slots - 1):
                    yield (child, *tail)


@lru_cache(maxsize=512)
def evaluate_candidates(glyphs: str, constraints: Constraints) -> tuple[Candidate, ...]:
    """
    Generate candidates covering exactly the specified signs within one word.

    :param glyphs: Consecutive signs, without word separators.
    :param constraints: Grouping and geometry limits.
    :return: Structurally permitted arrangements with geometry rejection reasons.
    :raises ValueError: If the input contains a word separator.
    """
    if any(glyph.isspace() for glyph in glyphs):
        raise ValueError("Candidate signs must belong to one word")
    size = len(glyphs)
    if size != 1 and not constraints.minimum_signs <= size <= constraints.maximum_signs:
        return ()
    return tuple(
        evaluate_arrangement(node, constraints)
        for node in _arrangements(glyphs, constraints.maximum_depth, constraints)
    )
