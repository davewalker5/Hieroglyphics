"""Score the geometry of valid automatic or manually constructed quadrats."""

from dataclasses import dataclass
from math import hypot

from hieroglyphics.composition.configuration import QUADRAT_SIZE, ScoringWeights
from hieroglyphics.composition.geometry import QuadratDrawing
from hieroglyphics.composition.sign_layout import sign_layout


@dataclass(frozen=True)
class InkBox:
    """Sign bounds measured in unscaled font units from the top left."""

    x: float
    y: float
    width: int
    height: int

    @property
    def area(self) -> int:
        """
        Get the area of the sign's bounding rectangle.

        :return: Area in square design units.
        """
        return self.width * self.height

    def distance(self, other: "InkBox") -> float:
        """
        Calculate the nearest distance between two rectangles.

        :param other: Another sign's bounds.
        :return: Distance in design units.
        """
        horizontal = max(0, self.x - other.x - other.width, other.x - self.x - self.width)
        vertical = max(0, self.y - other.y - other.height, other.y - self.y - self.height)
        return hypot(horizontal, vertical)


@dataclass(frozen=True)
class QuadratScore:
    """Normalised component scores followed by the weighted score."""

    efficiency: float
    relative_size: float
    aspect_ratio: float
    balance: float
    spacing: float
    overall: float


def score_quadrat(drawing: QuadratDrawing, weights: ScoringWeights) -> QuadratScore:
    """
    Score a validated drawing, preserving each sign's native proportions.

    :param drawing: Packed sign geometry using the intended rendering constraints.
    :param weights: Relative weights of the five scoring criteria.
    :return: Scores in [0, 1].
    """
    boxes = []
    for sign in drawing.signs:
        layout = sign_layout(sign.glyph)
        boxes.append(InkBox(sign.x + layout.left, sign.y - layout.top, layout.width, layout.height))

    area = sum(box.area for box in boxes)
    scale = drawing.scale
    efficiency = area * scale ** 2 / (drawing.spaced_width * QUADRAT_SIZE)
    relative_size = scale
    ratio = drawing.width / drawing.height
    target = drawing.constraints.target_aspect_ratio
    aspect_ratio = min(ratio / target, target / ratio)

    # Represent visual mass with each sign's ink bounding area.
    centre_x = sum(box.area * (box.x + box.width / 2) for box in boxes) / area
    centre_y = sum(box.area * (box.y + box.height / 2) for box in boxes) / area
    balance = 1 - max(abs(2 * centre_x / drawing.width - 1), abs(2 * centre_y / drawing.height - 1))
    spacing = _spacing_score(boxes, scale, drawing.constraints.sign_gap)

    components = (efficiency, relative_size, aspect_ratio, balance, spacing)
    values = (weights.efficiency, weights.relative_size, weights.aspect_ratio,
              weights.balance, weights.spacing)
    # Rescale first so even very large finite relative weights can be normalised.
    highest_weight = max(values)
    normalised = tuple(value / highest_weight for value in values)
    overall = sum(score * weight for score, weight in zip(components, normalised)) / sum(normalised)
    return QuadratScore(*components, overall)


def _spacing_score(boxes: list[InkBox], scale: float, preferred_gap: int) -> float:
    """
    Compare each sign's nearest neighbour clearance to the preferred gap.

    :param boxes: Unscaled sign bounds.
    :param scale: Uniform scale applied to the entire quadrat.
    :param preferred_gap: Desired clearance in rendered design units.
    :return: Mean clearance score in [0, 1].
    """
    if len(boxes) == 1:
        return 1.0
    distances = [
        min(box.distance(other) for other in boxes if other is not box) * scale
        for box in boxes
    ]
    return sum(min(gap / preferred_gap, preferred_gap / gap) for gap in distances) / len(boxes)
