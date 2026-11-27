"""Generate questions about documented uses of Egyptian hieroglyphs."""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.questions import Choice, Question


class LinguisticFunction(Enum):
    """The three roles covered by the exercise."""

    PHONOGRAM = "Phonogram"
    LOGOGRAM = "Logogram"
    DETERMINATIVE = "Determinative"


@dataclass(frozen=True)
class Scenario:
    """Teaching text for one documented function of a catalogue sign."""

    code_point: str
    function: LinguisticFunction
    context: str
    explanation: str

    @property
    def key(self) -> str:
        """
        Identify this scenario for avoiding immediate repeats.

        :return: Unicode code point paired with the function name.
        """
        return f"{self.code_point}:{self.function.name}"


@dataclass(frozen=True)
class FunctionQuestion(Question):
    """A question about one particular use of a catalogue sign."""

    scenario: Scenario
    sign: Sign
    other_functions: tuple[LinguisticFunction, ...]

    @property
    def repeat_key(self) -> str:
        """
        Identify the scenario to avoid immediate repeats.

        :return: Scenario identifier.
        """
        return self.scenario.key


_SCENARIO_PATH = Path(__file__).parent / "data" / "linguistic_function.json"


@lru_cache(maxsize=1)
def load_scenarios() -> tuple[Scenario, ...]:
    """
    Load the packaged scenarios, keyed by the sign and its intended function.

    :return: Scenarios in the order recorded in the data file.
    :raises ValueError: If a scenario repeats a sign and function.
    """
    records = json.loads(_SCENARIO_PATH.read_text(encoding="utf-8"))
    scenarios = tuple(
        Scenario(
            record["code_point"],
            LinguisticFunction[record["function"]],
            record["context"],
            record["explanation"],
        )
        for record in records
    )
    if len({scenario.key for scenario in scenarios}) != len(scenarios):
        raise ValueError("A sign and function are repeated in the scenario data.")
    return scenarios


def generate_function_question(
    signs: Iterable[Sign], randomizer: Random, previous_prompt: str = ""
) -> FunctionQuestion | None:
    """
    Ask learners to classify a sign's role in a stated use.

    :param signs: Available sign catalogue records.
    :param randomizer: Random generator for selecting a use and shuffling answers.
    :param previous_prompt: Scenario identifier to skip if another is available.
    :return: A question, or None when no scenario matches the catalogue.
    """
    signs_by_code_point = {sign.code_point: sign for sign in signs}
    scenarios = [
        scenario
        for scenario in load_scenarios()
        if scenario.code_point in signs_by_code_point
    ]
    if not scenarios:
        return None

    fresh = [scenario for scenario in scenarios if scenario.key != previous_prompt]
    scenarios_by_function: dict[LinguisticFunction, list[Scenario]] = {}
    for scenario in fresh or scenarios:
        scenarios_by_function.setdefault(scenario.function, []).append(scenario)

    # Sample the role first, so the larger phonogram pool cannot dominate.
    function = randomizer.choice(list(scenarios_by_function))
    scenario = randomizer.choice(scenarios_by_function[function])
    other_functions = tuple(
        other.function
        for other in scenarios
        if other.code_point == scenario.code_point and other.function != function
    )
    correct = Choice(function.name, function.value)
    choices = [Choice(role.name, role.value) for role in LinguisticFunction]
    randomizer.shuffle(choices)
    return FunctionQuestion(
        "What role does this sign play in the use described?",
        tuple(choices),
        correct,
        scenario,
        signs_by_code_point[scenario.code_point],
        other_functions,
    )
