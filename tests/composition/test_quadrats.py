"""Test grouping, geometry and preservation of sign order."""

import pytest

from hieroglyphics.composition.composer import compose
from hieroglyphics.composition.quadrat import Axis, Group, Node, Sign
from hieroglyphics.web.quadrat_renderer import QUADRAT_SIZE, render_quadrats


@pytest.mark.parametrize(
    ("glyphs", "expected"),
    [
        ("𓄿", (Sign("𓄿"),)),
        ("𓈖𓊃", (Group(Axis.VERTICAL, (Sign("𓈖"), Sign("𓊃"))),)),
        ("𓇋𓋴", (Group(Axis.HORIZONTAL, (Sign("𓇋"), Sign("𓋴"))),)),
        ("𓊪𓏏", (Group(Axis.VERTICAL, (Sign("𓊪"), Sign("𓏏"))),)),
        ("𓄿?", (Sign("𓄿"), Sign("?"))),
        ("𓈖𓊪𓏏", (Group(Axis.VERTICAL, (Sign("𓈖"), Sign("𓊪"), Sign("𓏏"))),)),
    ],
)
def test_composition_rules(glyphs: str, expected: tuple[Node, ...]) -> None:
    """
    Check deterministic grouping and standalone fallbacks.

    :param glyphs: Ordered input signs.
    :param expected: Expected quadrats for the input.
    """
    composition = compose([glyphs])
    assert composition.words == (expected,)
    assert composition == compose([glyphs])


def test_empty_words_and_word_boundaries() -> None:
    """Ignore empty words and keep compatible signs in separate words."""
    assert compose([""]).words == ()
    assert compose(["𓈖", "", "𓊃"]).words == ((Sign("𓈖"),), (Sign("𓊃"),))


def test_nested_drawing() -> None:
    """Check nested placement, sign order and maximum dimensions."""
    (drawing,), = render_quadrats(compose(["𓇋𓊪𓏏"]))
    tall, first_compact, second_compact = drawing.signs
    assert "".join(sign.glyph for sign in drawing.signs) == "𓇋𓊪𓏏"
    assert tall.x < first_compact.x
    assert first_compact.y < second_compact.y
    assert drawing.viewport_width <= QUADRAT_SIZE


def test_invalid_model() -> None:
    """Reject empty signs and groups without enough children."""
    with pytest.raises(ValueError, match="one character"):
        Sign("")
    with pytest.raises(ValueError, match="at least two"):
        Group(Axis.VERTICAL, (Sign("𓈖"),))
