"""Optimise complete words using candidate scores and transition costs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

from hieroglyphics.composition.candidates import Candidate, evaluate_candidates
from hieroglyphics.composition.configuration import (
    DEFAULT_SETTINGS, QUADRAT_SIZE, CompositionSettings,
)
from hieroglyphics.composition.quadrat import Composition, Node
from hieroglyphics.composition.scoring import QuadratScore, score_quadrat

MAX_CACHED_WORD_LENGTH = 128


@dataclass(frozen=True)
class CandidateDiagnostic:
    """One generated candidate at its offset in the original sign sequence."""

    start: int
    candidate: Candidate
    score: QuadratScore | None


@dataclass(frozen=True)
class SequenceResult:
    """One complete partition and its final score per source sign."""

    quadrats: tuple[Node, ...]
    score: float


@dataclass(frozen=True)
class WordDiagnostic:
    """Candidates and the best complete sequence ending in each valid final quadrat."""

    glyphs: str
    candidates: tuple[CandidateDiagnostic, ...]
    selected: SequenceResult
    alternatives: tuple[SequenceResult, ...]


@dataclass(frozen=True)
class _Path:
    """Best prefix ending in a specific quadrat."""

    candidate: Candidate
    value: float
    previous: _Path | None


def _sequence(path: _Path | None, size: int) -> SequenceResult:
    """
    Recover the selected path from its final quadrat.

    :param path: Final step, or None for a word without signs.
    :param size: Length of the source word in signs.
    :return: Complete sequence and its normalised score.
    """
    value = path.value if path else 0.0
    quadrats = []
    while path is not None:
        quadrats.append(path.candidate.node)
        path = path.previous
    return SequenceResult(tuple(reversed(quadrats)), value / size if size else 0.0)


def _transition(previous: Candidate, current: Candidate, settings: CompositionSettings) -> float:
    """
    Penalise additional quadrats and sudden changes in rendered height or scale.

    :param previous: Last quadrat of the preceding prefix.
    :param current: Next quadrat.
    :param settings: Sequence penalty weights.
    :return: Cost of this boundary.
    """
    first, second = previous.drawing, current.drawing
    height_change = abs(first.height * first.scale - second.height * second.scale) / QUADRAT_SIZE
    scale_change = abs(first.scale - second.scale)
    return settings.fragmentation_penalty + settings.consistency_penalty * (
        height_change + scale_change
    ) / 2


@lru_cache(maxsize=512)
def _score_candidate(candidate: Candidate, settings: CompositionSettings) -> QuadratScore:
    """
    Reuse component scores for repeated local sign sequences.

    :param candidate: Valid arrangement and its drawing.
    :param settings: Scoring configuration.
    :return: Component scores and their weighted result.
    """
    return score_quadrat(candidate.drawing, settings.weights)


def _search(
    glyphs: str, settings: CompositionSettings, diagnostics: list[CandidateDiagnostic] | None = None
) -> list[_Path]:
    """
    Keep only the best prefix for each possible final quadrat at each offset.

    :param glyphs: Sign sequence in one word.
    :param settings: Configuration for generation and scoring.
    :param diagnostics: Optional list to receive candidate evaluations.
    :return: Complete paths ordered by descending score, with stable ties.
    """
    paths: list[list[_Path]] = [[] for _ in range(len(glyphs) + 1)]
    # Weight each candidate by its sign count, so every partition scores the
    # same number of signs. Only the previous quadrat affects the next boundary.
    for start in range(len(glyphs)):
        for size in range(1, min(settings.constraints.maximum_signs, len(glyphs) - start) + 1):
            for candidate in evaluate_candidates(glyphs[start:start + size], settings.constraints):
                score = None if candidate.rejection else _score_candidate(candidate, settings)
                if diagnostics is not None:
                    diagnostics.append(CandidateDiagnostic(start, candidate, score))
                if score is None:
                    continue

                # Ties retain the first enumerated prefix and candidate.
                previous = None
                best_prefix = float("-inf") if start else 0.0
                for path in paths[start]:
                    prefix = path.value - _transition(path.candidate, candidate, settings)
                    if prefix > best_prefix:
                        previous, best_prefix = path, prefix
                value = score.overall * size + best_prefix
                paths[start + size].append(_Path(candidate, value, previous))

    return sorted(paths[-1], key=lambda path: path.value, reverse=True)


def _compose_word(glyphs: str, settings: CompositionSettings) -> tuple[Node, ...]:
    """
    Select the best complete partition of a word.

    :param glyphs: Signs in source order.
    :param settings: Composition configuration.
    :return: Ordered quadrats.
    """
    return _sequence(_search(glyphs, settings)[0], len(glyphs)).quadrats


_cached_word = lru_cache(maxsize=256)(_compose_word)


def compose(words: Iterable[str], settings: CompositionSettings = DEFAULT_SETTINGS) -> Composition:
    """
    Optimise each nonempty word independently, in logical reading order.

    :param words: Ordered glyph strings, one per source word.
    :param settings: Constraints and weights for this composition.
    :return: Composition in logical reading order.
    """
    return Composition(tuple(
        (_cached_word if len(word) <= MAX_CACHED_WORD_LENGTH else _compose_word)(word, settings)
        for word in words if word
    ))


def diagnose_word(glyphs: str, settings: CompositionSettings = DEFAULT_SETTINGS) -> WordDiagnostic:
    """
    Explain candidate rejection, scoring and choice of partition for a word.

    :param glyphs: Consecutive signs from one word.
    :param settings: Constraints and weights to investigate.
    :return: Candidate evaluations and representative complete partitions.
    """
    diagnostics: list[CandidateDiagnostic] = []
    paths = _search(glyphs, settings, diagnostics)
    sequences = tuple(_sequence(path, len(glyphs)) for path in paths)
    selected = sequences[0] if sequences else _sequence(None, 0)
    return WordDiagnostic(glyphs, tuple(diagnostics), selected, sequences[1:])
