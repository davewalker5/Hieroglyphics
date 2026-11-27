"""Track progress through a finite multiple-choice quiz."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class QuizRun:
    """The current question and cumulative score for one attempt."""

    limit: int
    seed: str
    answered: int = 0
    correct: int = 0
    previous_prompt: str = ""

    @property
    def complete(self) -> bool:
        """Return whether the attempt has reached its question limit."""
        return self.answered == self.limit

    @property
    def incorrect(self) -> int:
        """Return the number of incorrect answers."""
        return self.answered - self.correct

    @property
    def percentage(self) -> float:
        """Return the percentage of answered questions that were correct."""
        return 100 * self.correct / self.answered if self.answered else 0.0

    def record_answer(self, is_correct: bool, prompt: str, next_seed: str) -> "QuizRun":
        """
        Return progress after grading one answer.

        :param is_correct: Whether the learner selected the correct choice.
        :param prompt: The question just answered, to avoid repeating it next.
        :param next_seed: Seed for the next question.
        :return: Updated quiz progress.
        :raises ValueError: If the quiz is already complete.
        """
        if self.complete:
            raise ValueError("This quiz attempt is already complete.")
        return replace(
            self,
            seed=next_seed,
            answered=self.answered + 1,
            correct=self.correct + int(is_correct),
            previous_prompt=prompt,
        )
