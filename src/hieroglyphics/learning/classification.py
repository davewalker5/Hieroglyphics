"""Generate questions about Gardiner groups from the sign catalogue."""

from collections.abc import Iterable
from random import Random

from hieroglyphics.catalogue.signs import Sign, gardiner_group_name, group_label
from hieroglyphics.learning.questions import Choice, DisplayedSignQuestion

_DISTRACTOR_COUNT = 3
_PROMPT = "To which Gardiner group does this sign belong?"


def generate_classification_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> DisplayedSignQuestion | None:
    """
    Offer one documented group and three other distinct catalogue groups.

    :param signs: Available catalogue entries, each with a unique code point.
    :param randomizer: Random generator for selecting the sign and choices.
    :param previous_prompt: Code point to skip if another sign is available.
    :return: A question, or None if fewer than four groups are represented.
    """
    eligible = []
    for sign in signs:
        # Match the documented classification to the prefix of the Gardiner code.
        suffix = sign.gardiner.removeprefix(sign.group)
        if suffix[:1].isdigit() and gardiner_group_name(sign.group):
            eligible.append(sign)

    groups = sorted({sign.group for sign in eligible})
    if len(groups) <= _DISTRACTOR_COUNT:
        return None

    fresh = [sign for sign in eligible if sign.code_point != previous_prompt]
    sign = randomizer.choice(fresh or eligible)
    alternatives = [group for group in groups if group != sign.group]
    correct = Choice(sign.group, group_label(sign.group))
    choices = [
        correct,
        *(
            Choice(group, group_label(group))
            for group in randomizer.sample(alternatives, _DISTRACTOR_COUNT)
        ),
    ]
    randomizer.shuffle(choices)
    return DisplayedSignQuestion(_PROMPT, tuple(choices), correct, sign)
