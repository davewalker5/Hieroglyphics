"""Multiple-choice questions shared by learning exercises."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    """An answer identifier and its display text."""

    identifier: str
    text: str


@dataclass(frozen=True)
class Question:
    """A prompt with ordered choices and one correct answer."""

    prompt: str
    choices: tuple[Choice, ...]
    correct: Choice

    @property
    def repeat_key(self) -> str:
        """
        Identify the prompt for avoiding immediate repeats.

        :return: The prompt text by default.
        """
        return self.prompt

    def find_choice(self, identifier: str) -> Choice | None:
        """
        Resolve an answer submitted for this question.

        :param identifier: Identifier submitted by the learner.
        :return: The corresponding choice, if offered.
        """
        return next(
            (choice for choice in self.choices if choice.identifier == identifier),
            None,
        )
