"""Verify Gardiner question eligibility and answer generation."""

from random import Random

from hieroglyphics.catalogue.signs import Sign, get_catalogue, group_label
from hieroglyphics.learning.classification import generate_classification_question


def test_catalogue_questions_offer_one_matching_group() -> None:
    """Cover every supplied sign with distinct, labelled group choices."""
    signs = get_catalogue()[1]
    randomizer = Random(42)
    previous = ""
    seen = set()
    for _ in range(300):
        question = generate_classification_question(signs.values(), randomizer, previous)
        assert question is not None
        assert question.repeat_key != previous
        assert question.correct.identifier == question.sign.group
        assert len({choice.identifier for choice in question.choices}) == 4
        assert all(choice.text == group_label(choice.identifier) for choice in question.choices)
        assert all(" · " in choice.text for choice in question.choices)
        previous = question.repeat_key
        seen.add(question.sign.scalar)

    assert seen == set(signs)


def test_only_documented_matching_groups_count() -> None:
    """Reject choices with unknown names or a conflicting Gardiner prefix."""
    signs = [
        Sign(0x13000 + index, {"kEH_UniK": identifier, "kEH_Cat": group})
        for index, (identifier, group) in enumerate(
            [("A001", "A"), ("D001", "D"), ("G001", "G"), ("C001", "C"), ("M001", "N")]
        )
    ]
    assert generate_classification_question(signs, Random(42)) is None
