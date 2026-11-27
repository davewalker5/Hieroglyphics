"""Test distractor selection with overlapping and qualified catalogue values."""

from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.phonetic import generate_question


def test_shared_and_multiple_values() -> None:
    """Each generated prompt has one match even when readings overlap."""
    readings = ["wn | s", "m | wn", "s", "r", "n", "? | wn", ""]
    signs = [
        Sign(0x13000 + index, {"kEH_FVal": value})
        for index, value in enumerate(readings)
    ]
    values_by_id = {sign.code_point: sign.plain_phonetic_values for sign in signs}
    randomizer = Random(42)
    prompted_values = set()
    for _ in range(100):
        question = generate_question(signs, randomizer)
        assert question is not None
        value = question.prompt.removesuffix("?").split()[-1]
        prompted_values.add(value)
        assert len(set(question.choices)) == 4
        assert [
            choice
            for choice in question.choices
            if value in values_by_id[choice.identifier]
        ] == [question.correct]
        assert all(values_by_id[choice.identifier] for choice in question.choices)

    assert prompted_values == {"wn", "m", "s", "r", "n"}


def test_insufficient_choices() -> None:
    """Return no question if too few documented signs are available."""
    assert generate_question([Sign(0x13000, {"kEH_FVal": "wn"})], Random(42)) is None
