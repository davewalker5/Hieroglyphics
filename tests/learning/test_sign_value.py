"""Verify answer eligibility for questions about a displayed sign."""

from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.phonetic import generate_sign_value_question


def test_one_attested_choice_per_question() -> None:
    """Exclude every other reading of the sign from the unique choices."""
    readings = ["wn | s", "m | wn", "s", "r", "n", "? | k", ""]
    signs = [
        Sign(0x13000 + index, {"kEH_FVal": value})
        for index, value in enumerate(readings)
    ]
    randomizer = Random(42)
    previous_sign = ""
    seen = set()
    for _ in range(100):
        question = generate_sign_value_question(signs, randomizer, previous_sign)
        assert question is not None
        assert question.repeat_key != previous_sign
        assert len({choice.identifier for choice in question.choices}) == 4
        assert [
            choice
            for choice in question.choices
            if choice.text in question.sign.plain_phonetic_values
        ] == [question.correct]
        assert all(choice.text != "k" for choice in question.choices)
        seen.add(question.repeat_key)
        previous_sign = question.repeat_key

    assert seen == {sign.code_point for sign in signs[:5]}


def test_no_sign_with_enough_alternatives() -> None:
    """Return no question when every sign has fewer than three distractors."""
    signs = [
        Sign(0x13000, {"kEH_FVal": "wn | s"}),
        Sign(0x13001, {"kEH_FVal": "r | n"}),
    ]
    assert generate_sign_value_question(signs, Random(42)) is None
