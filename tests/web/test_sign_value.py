"""Exercise the sign-to-value quiz through its Flask routes."""

import re
from pathlib import Path

import pytest

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/sign-value"


@pytest.mark.parametrize("answer_correctly", [True, False])
def test_sign_value_quiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer_correctly: bool
) -> None:
    """
    Verify question, grading, catalogue feedback and final score.

    :param tmp_path: Directory for the quiz configuration.
    :param monkeypatch: Fixture for replacing config and question data.
    :param answer_correctly: Whether to choose an attested reading.
    """
    sign = Sign(0x130F9, {"kEH_FVal": "wn | wꜣ"})
    distractor_source = Sign(0x13000, {"kEH_FVal": "m | r | n"})
    signs = {entry.scalar: entry for entry in (sign, distractor_source)}
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.get_catalogue",
        lambda: ("test", signs),
    )
    config = tmp_path / "quiz.json"
    config.write_text('{"QUIZ_QUESTION_LIMIT": 1}', encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_QUIZ_CONFIG", str(config))
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex",
        lambda byte_count: "00" * byte_count,
    )
    client = create_app().test_client()

    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    assert f'aria-label="Displayed hieroglyph">{sign.glyph}</p>' in page
    assert "Question 1 of 1" in page
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    choices = re.findall(r'name="choice" value="([^"]+)"', page)
    assert len(set(choices)) == 4
    correct = next(choice for choice in choices if choice in sign.plain_phonetic_values)
    other_reading = next(
        value for value in sign.plain_phonetic_values if value != correct
    )
    assert other_reading not in choices
    assert ('id="transliteration-help"' in page) == (correct == "wꜣ")

    selected = correct if answer_correctly else "m"
    data = {"quiz": token, "choice": selected}
    assert client.post("/learn/phonetic-value", data=data).status_code == 400
    assert client.post(
        _EXERCISE_URL, data={"quiz": token, "choice": other_reading}
    ).status_code == 400

    response = client.post(_EXERCISE_URL, data=data)
    assert response.status_code == 200
    feedback = response.get_data(as_text=True)
    assert ("Correct!" if answer_correctly else "Incorrect.") in feedback
    assert f"<strong>{correct}</strong> is a documented reading" in feedback
    assert re.search(
        rf"Other documented readings\s*<strong>{other_reading}</strong>", feedback
    )
    assert f'href="/signs/{sign.code_point}"' in feedback
    assert "Quiz results" in feedback
    assert f"<strong>{100 if answer_correctly else 0}%</strong>" in feedback
    assert "Try again" in feedback
