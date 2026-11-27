"""Verify the linguistic function exercise through the Learn routes."""

import re
from pathlib import Path
from random import Random

import pytest

from hieroglyphics.catalogue.signs import get_catalogue
from hieroglyphics.learning.linguistic_function import generate_function_question
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/linguistic-function"


@pytest.mark.parametrize("answer_correctly", [True, False])
def test_linguistic_function_quiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer_correctly: bool
) -> None:
    """
    Check contextual prompts, answer feedback and quiz results.

    :param tmp_path: Directory for the quiz configuration.
    :param monkeypatch: Fixture for replacing the configuration and seed.
    :param answer_correctly: Whether to choose the role described in the prompt.
    """
    config = tmp_path / "quiz.json"
    config.write_text('{"QUIZ_QUESTION_LIMIT": 1}', encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_QUIZ_CONFIG", str(config))
    version, signs = get_catalogue()
    m18 = {0x131CD: signs[0x131CD]}
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.get_catalogue", lambda: (version, m18)
    )
    seed = "0" * 32
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex", lambda _: seed
    )
    client = create_app().test_client()
    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    question = generate_function_question(m18.values(), Random(seed))
    assert question is not None
    assert question.scenario.context in page
    assert 'aria-label="Displayed hieroglyph">𓇍</p>' in page
    assert "Other documented uses" not in page
    assert 'id="learn-catalogue-entry"' not in page
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    selected = question.correct.identifier if answer_correctly else "DETERMINATIVE"
    assert client.post(
        _EXERCISE_URL, data={"quiz": token, "choice": "UNKNOWN"}
    ).status_code == 400

    response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": selected})
    assert response.status_code == 200
    feedback = response.get_data(as_text=True)
    assert ("Correct!" if answer_correctly else "Incorrect.") in feedback
    assert question.scenario.explanation in feedback
    assert "Other documented uses of M18 include" in feedback
    assert 'href="/signs/U+131CD"' in feedback
    assert 'data-bs-toggle="modal" data-bs-target="#learn-catalogue-entry"' in feedback
    dialog = feedback.split('id="learn-catalogue-entry"', 1)[1]
    assert "Catalogue entry for M18" in dialog
    assert "<dt>Unicode</dt><dd>U+131CD</dd>" in dialog
    assert 'data-bs-dismiss="modal">Close</button>' in dialog
    assert client.get("/signs/U+131CD").status_code == 200
    assert "Quiz results" in feedback
    assert f"<strong>{100 if answer_correctly else 0}%</strong>" in feedback
