"""Exercise Phase 2.6 through the Learn page and the scoring flow."""

import re

import pytest

from hieroglyphics.catalogue.signs import get_catalogue
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/phonogram"


@pytest.mark.parametrize(
    ("scalar", "reading", "answer", "count", "correct"),
    [
        (0x13153, "m", "UNILITERAL", "1 consonant", True),
        (0x130F9, "wn", "BILITERAL", "2 consonants", True),
        (0x13124, "nfr", "BILITERAL", "3 consonants", False),
    ],
)
def test_phonogram_quiz(
    monkeypatch: pytest.MonkeyPatch,
    scalar: int,
    reading: str,
    answer: str,
    count: str,
    correct: bool,
) -> None:
    """
    Verify the prompt, three choices, explanatory feedback and final score.

    :param monkeypatch: Fixture for limiting the catalogue used by Learn.
    :param scalar: Code point of the sign used in the quiz.
    :param reading: Documented reading displayed in the prompt.
    :param answer: Submitted classification identifier.
    :param count: Expected consonant count in the feedback.
    :param correct: Whether the submitted classification is correct.
    """
    version, signs = get_catalogue()
    sign = signs[scalar]
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.get_catalogue",
        lambda: (version, {scalar: sign}),
    )
    app = create_app()
    app.config["QUIZ_QUESTION_LIMIT"] = 1
    client = app.test_client()
    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    assert f"when it represents {reading}?" in page
    assert f'aria-label="Displayed hieroglyph">{sign.glyph}</p>' in page
    assert set(re.findall(r'name="choice" value="([^"]+)"', page)) == {
        "UNILITERAL", "BILITERAL", "TRILITERAL"
    }
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]

    response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": answer})
    assert response.status_code == 200
    feedback = response.get_data(as_text=True)
    assert ("Correct!" if correct else "Incorrect.") in feedback
    assert f"{count} ({', '.join(reading)})." in " ".join(feedback.split())
    assert f'href="/signs/{sign.code_point}"' in feedback
    assert 'id="learn-catalogue-entry"' in feedback
    assert "Quiz results" in feedback
    assert f"<strong>{100 if correct else 0}%</strong>" in feedback
