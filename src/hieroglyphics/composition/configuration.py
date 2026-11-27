"""Practical limits and preferences for automatic quadrat composition."""

from dataclasses import dataclass
from math import isfinite

QUADRAT_SIZE = 1650  # Font design units in a full-size quadrat.


@dataclass(frozen=True)
class Constraints:
    """Grouping limits and geometry measured in bundled font design units."""

    minimum_signs: int = 1
    maximum_signs: int = 4
    maximum_vertical: int = 3
    maximum_horizontal: int = 3
    maximum_depth: int = 2
    target_aspect_ratio: float = 1.0
    variable_width: bool = True
    minimum_rendered_extent: int = 300
    maximum_reduction: float = 0.35
    minimum_aspect_ratio: float = 0.30
    maximum_aspect_ratio: float = 3.30
    minimum_sign_gap: int = 45
    sign_gap: int = 80
    minimum_quadrat_gap: int = 180

    def __post_init__(self) -> None:
        """
        Check that limits are consistent.

        :raises ValueError: If a grouping or geometry limit is invalid.
        """
        if not 1 <= self.minimum_signs <= self.maximum_signs:
            raise ValueError("Invalid minimum or maximum number of signs")
        if min(self.maximum_vertical, self.maximum_horizontal) < 1 or self.maximum_depth < 0:
            raise ValueError("Arrangement limits must be positive and depth nonnegative")
        if not (
            0 < self.minimum_aspect_ratio <= self.target_aspect_ratio <= self.maximum_aspect_ratio
        ):
            raise ValueError("Aspect ratio limits must surround a positive target")
        if not isfinite(self.maximum_aspect_ratio) or not 0 <= self.maximum_reduction < 1:
            raise ValueError("Aspect ratios must be finite and reduction must be in [0, 1)")
        if not 0 < self.minimum_rendered_extent <= QUADRAT_SIZE:
            raise ValueError("Minimum rendered extent must fit within a quadrat")
        if not 0 < self.minimum_sign_gap <= self.sign_gap or self.minimum_quadrat_gap < 0:
            raise ValueError("Spacing must allow separation between signs and quadrats")


@dataclass(frozen=True)
class ScoringWeights:
    """Relative weights for the five normalised quadrat scoring criteria."""

    efficiency: float = 0.30
    relative_size: float = 0.30
    aspect_ratio: float = 0.20
    balance: float = 0.15
    spacing: float = 0.05

    def __post_init__(self) -> None:
        """
        Validate the relative weights before normalisation.

        :raises ValueError: If any weight is invalid or all are zero.
        """
        values = (
            self.efficiency, self.relative_size, self.aspect_ratio, self.balance, self.spacing,
        )
        if any(not isfinite(value) or value < 0 for value in values) or not any(values):
            raise ValueError("Weights must be finite and nonnegative, with a positive weight")


@dataclass(frozen=True)
class CompositionSettings:
    """Constraints and weights plus per-boundary sequence penalties."""

    constraints: Constraints = Constraints()
    weights: ScoringWeights = ScoringWeights()
    fragmentation_penalty: float = 0.15
    consistency_penalty: float = 0.08

    def __post_init__(self) -> None:
        """
        Check that sequence penalties have a valid range.

        :raises ValueError: If a penalty is outside [0, 1].
        """
        if not all(0 <= value <= 1 for value in (
            self.fragmentation_penalty, self.consistency_penalty
        )):
            raise ValueError("Sequence penalties must be between zero and one")


DEFAULT_SETTINGS = CompositionSettings()
