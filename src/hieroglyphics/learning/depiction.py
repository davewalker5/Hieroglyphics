"""Generate object recognition questions from documented sign descriptions."""

import re
from collections.abc import Iterable
from random import Random
from unicodedata import normalize

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.questions import Choice, DisplayedSignQuestion

_DISTRACTOR_COUNT = 3
_PROMPT = "What does this hieroglyph depict?"
_QUALIFIED_DESCRIPTION = re.compile(
    r"\?|\b(?:or|perhaps|possibly|probably|likely|uncertain|unknown|unidentified|"
    r"unidentifiable|disputed|unclear|unconfirmed|tentative|maybe|apparently)\b",
    re.IGNORECASE,
)
_LEADING_ARTICLE = re.compile(r"^(?:a|an|the) ")


def _description_key(description: str) -> str:
    """
    Compare descriptions independently of articles, case and final punctuation.

    :param description: Catalogue description.
    :return: Comparison text for detecting duplicate answers.
    """
    text = " ".join(normalize("NFC", description).casefold().split())
    return _LEADING_ARTICLE.sub("", text).rstrip(".! ")


def generate_depiction_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> DisplayedSignQuestion | None:
    """
    Choose a sign and offer one documented depiction and three distinct alternatives.

    :param signs: Available catalogue entries, each with a unique code point.
    :param randomizer: Random generator for selecting the sign and answer order.
    :param previous_prompt: Code point to skip if another sign is available.
    :return: A question, or None if four suitable choices cannot be formed.
    """
    described_signs = [
        (sign, _description_key(sign.description))
        for sign in signs
        if sign.group
        and sign.description
        and not _QUALIFIED_DESCRIPTION.search(sign.description)
    ]
    eligible: list[tuple[Sign, list[Choice]]] = []
    for sign, key in described_signs:
        if not key:
            continue
        distractors: dict[str, Choice] = {}
        for alternative, alternative_key in described_signs:
            # Other groups keep closely related depictions out of introductory questions.
            if (
                alternative.group != sign.group
                and alternative_key
                and alternative_key != key
            ):
                distractors.setdefault(
                    alternative_key,
                    Choice(alternative.code_point, alternative.description),
                )
        if len(distractors) >= _DISTRACTOR_COUNT:
            eligible.append((sign, list(distractors.values())))

    if not eligible:
        return None
    fresh = [entry for entry in eligible if entry[0].code_point != previous_prompt]
    sign, distractors = randomizer.choice(fresh or eligible)
    correct = Choice(sign.code_point, sign.description)
    choices = [correct, *randomizer.sample(distractors, _DISTRACTOR_COUNT)]
    randomizer.shuffle(choices)
    return DisplayedSignQuestion(_PROMPT, tuple(choices), correct, sign)
