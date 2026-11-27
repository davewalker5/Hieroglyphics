"""Verify that questions distinguish roles in context."""

from random import Random

from hieroglyphics.catalogue.signs import get_catalogue
from hieroglyphics.learning.linguistic_function import (
    LinguisticFunction,
    generate_function_question,
    load_scenarios,
)


def test_context_distinguishes_two_roles_of_the_same_sign() -> None:
    """Cover all three roles and grade M18 according to the stated use."""
    randomizer = Random(42)
    previous = ""
    roles_by_glyph: dict[str, set[LinguisticFunction]] = {}
    signs = get_catalogue()[1]
    for _ in range(240):
        question = generate_function_question(signs.values(), randomizer, previous)
        assert question is not None
        scenario = question.scenario
        assert question.repeat_key != previous
        assert question.find_choice(scenario.function.name) == question.correct
        assert {choice.text for choice in question.choices} == {
            function.value for function in LinguisticFunction
        }
        assert scenario.context
        roles_by_glyph.setdefault(question.sign.glyph, set()).add(scenario.function)
        previous = question.repeat_key

    assert roles_by_glyph["𓇍"] == {
        LinguisticFunction.PHONOGRAM,
        LinguisticFunction.LOGOGRAM,
    }
    assert roles_by_glyph["𓀀"] == {LinguisticFunction.DETERMINATIVE}



def test_every_scenario_matches_a_catalogue_role() -> None:
    """Verify the curated roles against the properties in the generated catalogue."""
    source_labels = {
        LinguisticFunction.PHONOGRAM: "phonemogram",
        LinguisticFunction.LOGOGRAM: "logogram",
        LinguisticFunction.DETERMINATIVE: "classifier",
    }
    signs = {sign.code_point: sign for sign in get_catalogue()[1].values()}
    scenarios = load_scenarios()
    assert len(scenarios) == 28
    for scenario in scenarios:
        sign = signs[scenario.code_point]
        assert source_labels[scenario.function] in sign.properties["kEH_Func"].casefold()
        assert scenario.context and scenario.explanation

    assert generate_function_question([], Random(42)) is None
