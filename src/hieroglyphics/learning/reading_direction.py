"""Build illustrative horizontal rows with visible reading-direction clues."""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import permutations
from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.questions import Choice, Question

# These people, animals and birds clearly face left in the bundled font.
_FACING_SIGNS = (0x13000, 0x13050, 0x130F9, 0x1313F, 0x13171)
_WATER_RIPPLE = 0x13216
_LEFT_TO_RIGHT = Choice("left-to-right", "Left to right")
_RIGHT_TO_LEFT = Choice("right-to-left", "Right to left")


@dataclass(frozen=True)
class ReadingDirectionQuestion(Question):
    """A constructed sign sequence with signs stored in reading order."""

    signs: tuple[Sign, ...]

    @property
    def repeat_key(self) -> str:
        """
        Identify the same exercise sequence in either orientation.

        :return: The ordered code points of the sequence.
        """
        return " ".join(sign.code_point for sign in self.signs)

    @property
    def mirrored(self) -> bool:
        """
        Determine whether the left-facing glyphs should be flipped.

        :return: True when the row starts on the right.
        """
        return self.correct == _RIGHT_TO_LEFT


def generate_direction_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> ReadingDirectionQuestion | None:
    """
    Choose a constructed row flanked by two clearly facing signs.

    :param signs: Available catalogue entries.
    :param randomizer: Random generator for sign, direction and choice order.
    :param previous_prompt: Sequence to skip if a different one is available.
    :return: A question, or None if two directional signs are unavailable.
    """
    signs_by_scalar = {sign.scalar: sign for sign in signs}
    facing_signs = [
        signs_by_scalar[scalar] for scalar in _FACING_SIGNS if scalar in signs_by_scalar
    ]
    ripple = signs_by_scalar.get(_WATER_RIPPLE)
    middle = (ripple,) if ripple is not None else ()
    choices = [_LEFT_TO_RIGHT, _RIGHT_TO_LEFT]
    correct = randomizer.choice(choices)
    randomizer.shuffle(choices)
    questions = [
        ReadingDirectionQuestion(
            "In which direction should you read this row?",
            tuple(choices),
            correct,
            (first, *middle, last),
        )
        for first, last in permutations(facing_signs, 2)
    ]
    if not questions:
        return None
    fresh = [
        question for question in questions if question.repeat_key != previous_prompt
    ]
    return randomizer.choice(fresh or questions)
