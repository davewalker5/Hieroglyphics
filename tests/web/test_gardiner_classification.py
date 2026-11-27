"""Verify the Gardiner quiz through Learn and its catalogue popup."""

import re
from html import unescape

import pytest

from hieroglyphics.catalogue.signs import get_catalogue, group_label
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/gardiner-classification"


@pytest.mark.parametrize("answer_correctly", [True, False])
def test_gardiner_classification_quiz(
    monkeypatch: pytest.MonkeyPatch, answer_correctly: bool
) -> None:
    """
    Check question choices, answer feedback and results.

    :param monkeypatch: Fixture for controlling the question seed.
    :param answer_correctly: Whether to choose the sign's documented group.
    """
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex",
        lambda byte_count: "00" * byte_count,
    )
    app = create_app()
    app.config["QUIZ_QUESTION_LIMIT"] = 1
    client = app.test_client()

    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    glyph = re.search(r'aria-label="Displayed hieroglyph">(.)</p>', page)[1]
    sign = get_catalogue()[1][ord(glyph)]
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    choices = re.findall(r'name="choice" value="([^"]+)"', page)
    assert len(set(choices)) == 4
    assert sign.group in choices
    assert sign.gardiner not in choices
    assert 'id="learn-catalogue-entry"' not in page

    selected = sign.group if answer_correctly else next(
        choice for choice in choices if choice != sign.group
    )
    response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": selected})
    assert response.status_code == 200
    feedback = unescape(response.get_data(as_text=True))
    assert ("Correct!" if answer_correctly else "Incorrect.") in feedback
    assert f"<strong>{group_label(sign.group)}</strong>" in feedback
    assert sign.description in feedback
    assert f"<dt>Gardiner identifier</dt><dd>{sign.gardiner}</dd>" in feedback
    assert 'data-bs-toggle="modal" data-bs-target="#learn-catalogue-entry"' in feedback
    assert f"Catalogue entry for {sign.gardiner}" in feedback
    assert "Quiz results" in feedback
    assert f"<strong>{100 if answer_correctly else 0}%</strong>" in feedback
