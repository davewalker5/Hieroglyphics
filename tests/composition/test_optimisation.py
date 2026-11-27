"""Check candidate limits, scoring and complete-word optimisation."""

from dataclasses import astuple, replace

import pytest

from hieroglyphics.composition.candidates import evaluate_arrangement, evaluate_candidates
from hieroglyphics.composition.composer import compose, diagnose_word
from hieroglyphics.composition.configuration import DEFAULT_SETTINGS, Constraints, ScoringWeights
from hieroglyphics.composition.quadrat import Axis, Group, Sign
from hieroglyphics.composition.scoring import score_quadrat


def test_candidate_shapes_and_depth() -> None:
    """Generate both axes, triples, and four-sign trees subject to depth limits."""
    constraints = Constraints()
    pair = evaluate_candidates("𓊪𓏏", constraints)
    assert {item.node.axis for item in pair if isinstance(item.node, Group)} == set(Axis)
    triples = evaluate_candidates("𓈖𓊪𓏏", constraints)
    assert {item.node.axis for item in triples if len(item.node.children) == 3} == set(Axis)

    candidates = evaluate_candidates("𓊪𓏏𓊪𓏏", constraints)
    assert any(item.rejection is None for item in candidates)
    assert not evaluate_candidates("𓊪𓏏𓊪𓏏", replace(constraints, maximum_depth=1))
    assert not evaluate_candidates("𓊪𓏏𓊪𓏏", replace(constraints, maximum_signs=3))
    for item in candidates:
        assert "".join(sign.glyph for sign in item.drawing.signs) == "𓊪𓏏𓊪𓏏"


def test_constraints_and_single_sign_fallback() -> None:
    """Reject disallowed groups and preserve the independent sign fallback."""
    constraints = Constraints(minimum_signs=2, maximum_reduction=0.0)
    assert evaluate_candidates("𓊪", constraints)[0].rejection is None
    assert all(item.rejection for item in evaluate_candidates("𓊪?", constraints))
    with pytest.raises(ValueError, match="one word"):
        evaluate_candidates("𓊪 𓏏", constraints)
    group = Group(Axis.HORIZONTAL, (Sign("𓄿"), Sign("𓄿")))
    assert evaluate_arrangement(group, constraints).rejection == "Excessive uniform scaling"
    assert "depth" in evaluate_arrangement(group, replace(constraints, maximum_depth=0)).rejection


def test_weighted_geometry_scores() -> None:
    """Prefer packing wide signs vertically and apply individual score weights."""
    constraints = Constraints()
    candidates = evaluate_candidates("𓈖𓈖", constraints)
    rows = {item.node.axis: item.drawing for item in candidates}
    weights = ScoringWeights()
    stack = score_quadrat(rows[Axis.VERTICAL], weights)
    line = score_quadrat(rows[Axis.HORIZONTAL], weights)
    assert all(0 <= value <= 1 for value in astuple(stack))
    assert stack.efficiency > line.efficiency
    assert stack.relative_size > line.relative_size
    assert stack.overall > line.overall
    aspect_only = ScoringWeights(0, 0, 2, 0, 0)
    score = score_quadrat(rows[Axis.VERTICAL], aspect_only)
    assert score.overall == pytest.approx(score.aspect_ratio)


def test_dynamic_programming_matches_exhaustive_small_word() -> None:
    """Find the best complete partition, with the same sign count in every partition."""
    glyphs = "𓇋𓇋𓋴𓋴"
    settings = replace(DEFAULT_SETTINGS, consistency_penalty=0)
    values: list[list[float]] = [[0.0], [], [], [], []]
    for start, prefixes in enumerate(values[:-1]):
        for end in range(start + 1, len(glyphs) + 1):
            for item in evaluate_candidates(glyphs[start:end], settings.constraints):
                if item.rejection is None:
                    value = score_quadrat(item.drawing, settings.weights).overall * (end - start)
                    penalty = settings.fragmentation_penalty if start else 0
                    values[end].extend(prefix + value - penalty for prefix in prefixes)

    diagnostic = diagnose_word(glyphs, settings)
    assert diagnostic.selected.score == pytest.approx(max(values[-1]) / len(glyphs))
    assert diagnostic.alternatives
    assert diagnostic == diagnose_word(glyphs, settings)
    assert diagnostic.selected.quadrats == compose([glyphs], settings).words[0]
    assert compose([glyphs, glyphs], settings).words == (diagnostic.selected.quadrats,) * 2
    assert any(item.score is None and item.candidate.rejection for item in diagnostic.candidates)


def test_fragmentation_and_readability() -> None:
    """Group compatible signs while keeping large signs independent when necessary."""
    assert len(compose(["𓇋𓊪𓏏"]).words[0]) == 1
    assert compose(["𓄿𓄿"]).words[0] == (Sign("𓄿"), Sign("𓄿"))
