"""Check the Learn navigation, answer feedback and question progression."""

import re
from html import unescape
from pathlib import Path
from random import Random

import pytest
from flask.testing import FlaskClient

from hieroglyphics.catalogue.signs import get_catalogue
from hieroglyphics.learning.phonetic import generate_question
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/phonetic-value"


@pytest.fixture
def client() -> FlaskClient:
    """
    Create a test client for the normal application entry point.

    :return: Client with the Learn blueprint registered.
    """
    return create_app().test_client()


@pytest.mark.parametrize("answer_correctly", [True, False])
def test_phonetic_exercise(client: FlaskClient, answer_correctly: bool) -> None:
    """
    Follow Learn navigation, answer a question and start the next one.

    :param client: Test client for the application.
    :param answer_correctly: Whether to select the matching sign.
    """
    assert 'href="/learn/"' in client.get("/", follow_redirects=True).get_data(
        as_text=True
    )
    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    value = re.search(r"attested phonetic value (.*?)\?</h2>", page)[1]
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    choices = re.findall(r'name="choice" value="(U\+[0-9A-F]+)"', page)
    assert len(set(choices)) == 4

    signs = get_catalogue()[1]
    matches = [
        choice
        for choice in choices
        if value in signs[int(choice[2:], 16)].plain_phonetic_values
    ]
    assert len(matches) == 1
    correct = matches[0]
    selected = (
        correct
        if answer_correctly
        else next(choice for choice in choices if choice != correct)
    )

    # Opening another question must leave the original form answerable.
    client.get(_EXERCISE_URL)
    response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": selected})
    assert response.status_code == 200
    feedback = response.get_data(as_text=True)
    assert ("Correct!" if answer_correctly else "Incorrect.") in feedback
    assert f'href="/signs/{correct}"' in feedback
    assert signs[int(correct[2:], 16)].description in unescape(feedback)
    assert "Next question" in feedback

    next_token = re.search(r'name="quiz" value="([^"]+)"', feedback)[1]
    next_page = client.get(_EXERCISE_URL, query_string={"quiz": next_token}).get_data(
        as_text=True
    )
    assert f"attested phonetic value {value}?" not in next_page
    assert "Question 2 of 10" in next_page
    next_choice = re.search(r'name="choice" value="([^"]+)"', next_page)[1]
    assert (
        client.post(
            _EXERCISE_URL, data={"quiz": next_token, "choice": next_choice}
        ).status_code
        == 200
    )


def test_reject_invalid_submission(client: FlaskClient) -> None:
    """
    Reject altered quiz progress and choices outside the question.

    :param client: Test client for the application.
    """
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    for data in (
        {"choice": "U+13153"},
        {"quiz": token + "invalid", "choice": "U+13153"},
        {"quiz": token, "choice": "U+13000"},
        {"quiz": token, "choice": ""},
    ):
        assert client.post(_EXERCISE_URL, data=data).status_code == 400


@pytest.mark.parametrize(
    ("answers", "expected_score"), [([False], "0%"), ([True, False, True], "66.7%")]
)
def test_quiz_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    answers: list[bool],
    expected_score: str,
) -> None:
    """
    Play a configured quiz, verify results, and start a fresh attempt.

    :param tmp_path: Directory for the quiz configuration.
    :param monkeypatch: Environment patching fixture.
    :param answers: Whether to answer each question correctly.
    :param expected_score: Expected percentage on the results screen.
    """
    limit = len(answers)
    config = tmp_path / "quiz.json"
    config.write_text(f'{{"QUIZ_QUESTION_LIMIT": {limit}}}', encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_QUIZ_CONFIG", str(config))
    client = create_app().test_client()
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    signs = get_catalogue()[1]
    for number, correct in enumerate(answers, start=1):
        assert f"Question {number} of {limit}" in page
        assert 'href="/learn/">← Learn</a>' in page
        value = re.search(r"attested phonetic value (.*?)\?</h2>", page)[1]
        choices = re.findall(r'name="choice" value="(U\+[0-9A-F]+)"', page)
        choice = next(
            identifier
            for identifier in choices
            if (value in signs[int(identifier[2:], 16)].plain_phonetic_values)
            == correct
        )
        token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
        response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": choice})
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        if number < limit:
            assert "Quiz results" not in page
            token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
            page = client.get(_EXERCISE_URL, query_string={"quiz": token}).get_data(
                as_text=True
            )

    assert re.search(
        r'</section>\s*<section class="workspace-panel learn-results" '
        'aria-labelledby="quiz-results">',
        page,
    )
    assert f"<strong>{sum(answers)} / {limit}</strong>" in page
    assert f'id="quiz-correct" value="{sum(answers)}" max="{limit}"' in page
    assert f"<strong>{expected_score}</strong>" in page
    assert (
        f'id="quiz-percentage" value="{100 * sum(answers) / limit}" max="100"' in page
    )
    assert f"Incorrect answers <strong>{limit - sum(answers)}</strong>" in page
    assert "Next question" not in page
    assert "Try again" in page
    assert 'href="/learn/">← Learn</a>' in page
    assert "Back to Learn" not in page
    assert f"Question 1 of {limit}" in client.get(_EXERCISE_URL).get_data(as_text=True)


@pytest.mark.parametrize("limit", ["0", "-1", "true", "2.5", '"3"'])
def test_invalid_quiz_length(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """
    Reject quiz lengths that are not positive integers.

    :param tmp_path: Directory for the quiz configuration.
    :param monkeypatch: Environment patching fixture.
    :param limit: Invalid JSON value for the question limit.
    """
    config = tmp_path / "quiz.json"
    config.write_text(f'{{"QUIZ_QUESTION_LIMIT": {limit}}}', encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_QUIZ_CONFIG", str(config))
    with pytest.raises(
        ValueError, match="QUIZ_QUESTION_LIMIT must be a positive integer"
    ):
        create_app()


@pytest.mark.parametrize(
    ("value", "has_help"),
    [
        ("ḳ", True),
        ("k", False),
        ("ꜣ", True),
        ("ꞽ", True),
        ("wꜣ", True),
        ("ḏ", True),
    ],
)
def test_transliteration_help(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    has_help: bool,
) -> None:
    """
    Render the local help dialog only for readings covered by its table.

    :param client: Test client for the application.
    :param monkeypatch: Environment patching fixture.
    :param value: Reading expected in the prompt.
    :param has_help: Whether the reading should have a help button.
    """
    signs = get_catalogue()[1].values()
    seed = next(
        candidate
        for candidate in range(1_000)
        if (question := generate_question(signs, Random(f"{candidate:032x}")))
        and question.value == value
    )
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex",
        lambda byte_count: f"{seed:0{2 * byte_count}x}",
    )
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    assert f"attested phonetic value {value}?" in page
    assert ('data-bs-target="#transliteration-help"' in page) == has_help
    assert ('id="transliteration-help"' in page) == has_help
    if has_help:
        assert 'type="button" data-bs-dismiss="modal"' in page
        dialog = page.split('id="transliteration-help"', 1)[1]
        assert "Sign in the quiz" not in dialog
        assert not any(glyph in dialog for glyph in "𓄿𓇋𓈎𓆓𓍯")
        assert all(
            f'<th scope="row">{reading}</th>' in page
            for reading in ("ꜣ", "ꞽ", "ḳ", "ḏ", "wꜣ")
        )
