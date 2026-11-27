"""Generate sign recognition questions from documented phonetic values."""

from collections.abc import Iterable
from dataclasses import dataclass
from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.questions import Choice, DisplayedSignQuestion, Question

_CHOICE_COUNT = 4
_GUIDE_CHARACTERS = frozenset("ꜣꞽḳḏ")


@dataclass(frozen=True)
class PhoneticQuestion(Question):
    """A sign-recognition question with the original transliteration value."""

    value: str
    sign: Sign

    @property
    def has_transliteration_help(self) -> bool:
        """Return whether the prompt contains a character covered by the guide."""
        return not _GUIDE_CHARACTERS.isdisjoint(self.value)


def _prompt(value: str) -> str:
    """
    Phrase a question about one documented value.

    :param value: Transliteration from the catalogue.
    :return: The question shown to the learner.
    """
    return f"Which sign has the attested phonetic value {value}?"


def generate_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> PhoneticQuestion | None:
    """
    Build a question with exactly one choice documenting the prompted value.

    :param signs: Available catalogue entries, each with a unique code point.
    :param randomizer: Random generator for choosing the value and sign order.
    :param previous_prompt: Prompt to skip if another is available.
    :return: A question, or None if four unambiguous choices cannot be formed.
    """
    signs_by_choice: dict[Choice, Sign] = {}
    values_by_sign: dict[Choice, tuple[str, ...]] = {}
    for sign in signs:
        values = sign.plain_phonetic_values
        if values:
            choice = Choice(sign.code_point, sign.glyph)
            signs_by_choice[choice] = sign
            values_by_sign[choice] = values

    candidates_by_value: dict[str, list[Choice]] = {}
    for choice, values in values_by_sign.items():
        for value in values:
            candidates_by_value.setdefault(value, []).append(choice)

    # Only signs with documented, unqualified readings enter the choice pool.
    playable_values = [
        value
        for value, candidates in candidates_by_value.items()
        if len(values_by_sign) - len(candidates) >= _CHOICE_COUNT - 1
    ]
    if not playable_values:
        return None

    new_values = [
        value for value in playable_values if _prompt(value) != previous_prompt
    ]
    value = randomizer.choice(new_values or playable_values)
    correct = randomizer.choice(candidates_by_value[value])
    distractors = [
        choice for choice, values in values_by_sign.items() if value not in values
    ]
    choices = [correct, *randomizer.sample(distractors, _CHOICE_COUNT - 1)]
    randomizer.shuffle(choices)
    return PhoneticQuestion(
        _prompt(value), tuple(choices), correct, value, signs_by_choice[correct]
    )


_VALUE_PROMPT = "Which of these is an attested phonetic value of the displayed sign?"


@dataclass(frozen=True)
class SignValueQuestion(DisplayedSignQuestion):
    """A question asking for one documented reading of the displayed sign."""

    @property
    def has_transliteration_help(self) -> bool:
        """Return whether any choice contains a character covered by the guide."""
        return any(
            not _GUIDE_CHARACTERS.isdisjoint(choice.text) for choice in self.choices
        )


def generate_sign_value_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> SignValueQuestion | None:
    """
    Choose a sign with exactly one attested reading among the offered choices.

    :param signs: Available catalogue entries, each with a unique code point.
    :param randomizer: Random generator for choosing the sign and readings.
    :param previous_prompt: Code point to skip if another sign is available.
    :return: A question, or None if four unambiguous choices cannot be formed.
    """
    readings_by_sign = [(sign, sign.plain_phonetic_values) for sign in signs]
    readings = dict.fromkeys(
        value for _, values in readings_by_sign for value in values
    )
    eligible = [
        (sign, values)
        for sign, values in readings_by_sign
        if values and len(readings) - len(values) >= _CHOICE_COUNT - 1
    ]
    if not eligible:
        return None

    fresh = [
        (sign, values)
        for sign, values in eligible
        if sign.code_point != previous_prompt
    ]
    sign, values = randomizer.choice(fresh or eligible)
    value = randomizer.choice(values)
    # Exclude every reading of the displayed sign, including alternate readings.
    alternatives = [reading for reading in readings if reading not in values]
    correct = Choice(value, value)
    choices = [
        correct,
        *(
            Choice(reading, reading)
            for reading in randomizer.sample(alternatives, _CHOICE_COUNT - 1)
        ),
    ]
    randomizer.shuffle(choices)
    return SignValueQuestion(_VALUE_PROMPT, tuple(choices), correct, sign)
