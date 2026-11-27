"""Verify the depicted object quiz through Learn and the catalogue."""

import re
from html import unescape
from pathlib import Path

import pytest

from hieroglyphics.catalogue.signs import get_catalogue, group_label
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/depicted-object"


@pytest.mark.parametrize("answer_correctly", [True, False])
def test_depicted_object_quiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer_correctly: bool
) -> None:
    """
    Play a one-question quiz and check feedback, catalogue access and scoring.

    :param tmp_path: Directory for the quiz configuration.
    :param monkeypatch: Fixture for selecting the configuration and quiz seed.
    :param answer_correctly: Whether to choose the correct description.
    """
    config = tmp_path / "quiz.json"
    config.write_text('{"QUIZ_QUESTION_LIMIT": 1}', encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_QUIZ_CONFIG", str(config))
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex",
        lambda byte_count: "00" * byte_count,
    )
    client = create_app().test_client()
    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    response = client.get(_EXERCISE_URL)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Question 1 of 1" in page
    glyph = re.search(r'aria-label="Displayed hieroglyph">(.)</p>', page)[1]
    sign = get_catalogue()[1][ord(glyph)]
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    choices = re.findall(r'name="choice" value="([^"]+)"', page)
    assert len(set(choices)) == 4
    assert sign.code_point in choices
    assert sign.description in unescape(page)
    assert "Gardiner identifier" not in page
    assert 'id="learn-catalogue-entry"' not in page
    assert 'id="transliteration-help"' not in page

    selected = sign.code_point if answer_correctly else next(
        choice for choice in choices if choice != sign.code_point
    )
    data = {"quiz": token, "choice": selected}
    assert client.post("/learn/sign-value", data=data).status_code == 400
    response = client.post(_EXERCISE_URL, data=data)
    assert response.status_code == 200
    feedback = unescape(response.get_data(as_text=True))
    assert ("Correct!" if answer_correctly else "Incorrect.") in feedback
    assert f"<strong>{sign.description}</strong>" in feedback
    assert f"<dt>Gardiner identifier</dt><dd>{sign.gardiner}</dd>" in feedback
    assert group_label(sign.group) in feedback
    for key, label in (
        ("kEH_FVal", "Documented phonetic value"),
        ("kEH_Func", "Linguistic function"),
    ):
        if sign.properties.get(key):
            assert f"<dt>{label}</dt><dd>{sign.properties[key]}</dd>" in feedback
    catalogue_url = f"/signs/{sign.code_point}"
    assert f'href="{catalogue_url}"' in feedback
    assert 'data-bs-toggle="modal" data-bs-target="#learn-catalogue-entry"' in feedback
    dialog = feedback.split('id="learn-catalogue-entry"', 1)[1]
    assert "Letters that use this sign in the app" in dialog
    assert f"<dt>Unicode</dt><dd>{sign.code_point}</dd>" in dialog
    assert 'data-bs-dismiss="modal">Close</button>' in dialog
    catalogue_page = client.get(catalogue_url)
    assert catalogue_page.status_code == 200
    assert "Letters that use this sign in the app" in catalogue_page.get_data(as_text=True)
    assert "Its reading and meaning in an inscription depend on context." in feedback
    assert "Quiz results" in feedback
    assert f"<strong>{100 if answer_correctly else 0}%</strong>" in feedback
    assert "Try again" in feedback
