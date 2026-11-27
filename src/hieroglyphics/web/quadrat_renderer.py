"""Prepare quadrat drawings for the shared SVG template."""

from hieroglyphics.composition.configuration import DEFAULT_SETTINGS, QUADRAT_SIZE, Constraints
from hieroglyphics.composition.geometry import QuadratDrawing, draw_quadrat
from hieroglyphics.composition.quadrat import Composition

__all__ = ["QUADRAT_SIZE", "render_quadrats"]


def render_quadrats(
    composition: Composition, constraints: Constraints = DEFAULT_SETTINGS.constraints
) -> tuple[tuple[QuadratDrawing, ...], ...]:
    """
    Prepare SVG drawings while preserving word boundaries and reading order.

    :param composition: Ordered words and quadrats.
    :param constraints: The same geometry configuration used for composition.
    :return: Per-word drawings with direction-independent geometry.
    """
    return tuple(
        tuple(draw_quadrat(node, constraints) for node in word) for word in composition.words
    )
