"""Verify eligibility and distractor selection for depicted object questions."""

from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.depiction import generate_depiction_question


def test_only_distinct_documented_depictions_are_offered() -> None:
    """Exclude uncertain depictions, near duplicates and same-group alternatives."""
    entries = [
        ("E", "A hare."),
        ("I", "The hare"),
        ("G", "An owl."),
        ("G", " Owl "),
        ("I", "A viper."),
        ("D", "A mouth."),
        ("M", "A reed."),
        ("O", "A courtyard or reed shelter."),
        ("O", "Possibly a house."),
        ("W", "A jar?"),
        ("W", ""),
    ]
    signs = [
        Sign(0x13000 + index, {"kEH_Desc": description, "kEH_Cat": group})
        for index, (group, description) in enumerate(entries)
    ]
    signs_by_id = {sign.code_point: sign for sign in signs}
    previous = ""
    seen = set()
    randomizer = Random(42)
    for _ in range(100):
        question = generate_depiction_question(signs, randomizer, previous)
        assert question is not None
        assert question.repeat_key != previous
        assert question.correct.text == question.sign.description
        assert len(question.choices) == 4
        offered = {choice.identifier for choice in question.choices}
        assert not {sign.code_point for sign in signs[7:]} & offered
        assert not {signs[0].code_point, signs[1].code_point} <= offered
        assert not {signs[2].code_point, signs[3].code_point} <= offered
        assert all(
            signs_by_id[choice.identifier].group != question.sign.group
            for choice in question.choices
            if choice != question.correct
        )
        previous = question.repeat_key
        seen.add(previous)

    assert seen == {sign.code_point for sign in signs[:7]}


def test_no_question_with_insufficient_distinct_alternatives() -> None:
    """Report an empty pool when repeated descriptions cannot fill four choices."""
    descriptions = [
        ("G", "An owl."),
        ("E", "A hare."),
        ("D", "A mouth."),
        ("X", "The mouth"),
    ]
    signs = [
        Sign(0x13000 + index, {"kEH_Desc": description, "kEH_Cat": group})
        for index, (group, description) in enumerate(descriptions)
    ]
    assert generate_depiction_question(signs, Random(42)) is None
