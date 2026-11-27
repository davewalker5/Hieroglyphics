"""Generate questions about the consonants represented by phonograms."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.questions import Choice, DisplayedSignQuestion


class PhonogramClass(Enum):
    """Classifications keyed by the number of consonants in a reading."""

    UNILITERAL = 1
    BILITERAL = 2
    TRILITERAL = 3


@dataclass(frozen=True)
class PhonogramQuestion(DisplayedSignQuestion):
    """A classification question about one documented reading of a sign."""

    reading: str
    consonants: tuple[str, ...]


def generate_phonogram_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> PhonogramQuestion | None:
    """
    Ask how many consonants a sign represents in a specific phonogram use.

    :param signs: Available catalogue entries.
    :param randomizer: Random generator for choosing a reading and ordering answers.
    :param previous_prompt: Code point to skip if another sign is available.
    :return: A question, or None when no confirmed phonogram reading is available.
    """
    readings: list[tuple[Sign, str]] = []
    for sign in signs:
        if sign.properties.get("kEH_Func", "").casefold() == "phonemogram":
            readings.extend((sign, value) for value in sign.plain_phonetic_values)
    if not readings:
        return None

    fresh = [entry for entry in readings if entry[0].code_point != previous_prompt]
    readings_by_class: dict[PhonogramClass, list[tuple[Sign, str]]] = {}
    for sign, value in fresh or readings:
        # The catalogue validates NFC readings against single-consonant symbols.
        classification = PhonogramClass(len(value))
        readings_by_class.setdefault(classification, []).append((sign, value))

    # Pick a class first so the many uniliteral signs do not dominate.
    classification = randomizer.choice(list(readings_by_class))
    sign, reading = randomizer.choice(readings_by_class[classification])
    choices_by_class = {
        member: Choice(member.name, f"{member.name.title()} phonogram")
        for member in PhonogramClass
    }
    choices = list(choices_by_class.values())
    randomizer.shuffle(choices)
    return PhonogramQuestion(
        f"How is this sign classified when it represents {reading}?",
        tuple(choices),
        choices_by_class[classification],
        sign,
        reading,
        tuple(reading),
    )
