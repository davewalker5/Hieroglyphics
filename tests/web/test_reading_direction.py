"""Verify that the reading-direction quiz mirrors glyphs and reverses their order."""

import re
from random import Random

import pytest

from hieroglyphics.catalogue.signs import get_catalogue
from hieroglyphics.learning.reading_direction import generate_direction_question
from hieroglyphics.web import create_app

_EXERCISE_URL = "/learn/reading-direction"


@pytest.mark.parametrize(
    ("seed", "facing", "answer", "correct"),
    [
        ("b", "left", "left-to-right", True),
        ("a", "right", "left-to-right", False),
    ],
)
def test_reading_direction_quiz(
    monkeypatch: pytest.MonkeyPatch,
    seed: str,
    facing: str,
    answer: str,
    correct: bool,
) -> None:
    """
    Check both orientations through the question, feedback and results pages.

    :param monkeypatch: Fixture for fixing the quiz seed.
    :param seed: Seed that selects the target orientation.
    :param facing: Side that the figures in the question face.
    :param answer: Submitted reading direction.
    :param correct: Whether the submitted direction is correct.
    """
    monkeypatch.setattr(
        "hieroglyphics.web.learn.learn_blueprint.token_hex", lambda _: seed
    )
    question = generate_direction_question(get_catalogue()[1].values(), Random(seed))
    assert question is not None

    app = create_app()
    app.config["QUIZ_QUESTION_LIMIT"] = 1
    client = app.test_client()
    assert f'href="{_EXERCISE_URL}"' in client.get("/learn/").get_data(as_text=True)
    page = client.get(_EXERCISE_URL).get_data(as_text=True)
    assert "constructed examples" in page
    assert f"figures facing {facing}" in page
    assert "learn-direction-clue" not in page
    assert set(re.findall(r'name="choice" value="([^"]+)"', page)) == {
        "left-to-right",
        "right-to-left",
    }
    reading_order = [sign.glyph for sign in question.signs]
    visual_order = reading_order if facing == "left" else reading_order[::-1]
    glyph_class = "l-to-r" if facing == "left" else "r-to-l"
    opposite_class = "r-to-l" if facing == "left" else "l-to-r"
    glyph_pattern = r'class="hieroglyph-cell-([lr]-to-[lr])">([^<]+)</span>'
    assert re.findall(glyph_pattern, page) == [
        (glyph_class, glyph) for glyph in visual_order
    ]

    token = re.search(r'name="quiz" value="([^"]+)"', page)[1]
    response = client.post(_EXERCISE_URL, data={"quiz": token, "choice": answer})
    assert response.status_code == 200
    feedback = response.get_data(as_text=True)
    assert ("Correct!" if correct else "Incorrect.") in feedback
    assert f"Begin at the {facing} edge" in feedback
    assert feedback.count("learn-direction-clue") == 4
    assert re.findall(glyph_pattern, feedback) == [
        *((glyph_class, glyph) for glyph in visual_order),
        *((opposite_class, glyph) for glyph in reversed(visual_order)),
    ]
    assert "Quiz results" in feedback
    assert f"<strong>{100 if correct else 0}%</strong>" in feedback


def test_direction_questions_require_two_facing_signs() -> None:
    """A neutral sign cannot supply a missing directional clue."""
    signs = get_catalogue()[1]
    incomplete_row = [signs[0x13000], signs[0x13216]]
    assert generate_direction_question(incomplete_row, Random(0)) is None


def test_direction_question_avoids_repeating_the_sequence() -> None:
    """Changing orientation alone does not count as a new sequence."""
    signs = get_catalogue()[1].values()
    question = generate_direction_question(signs, Random(0))
    assert question is not None
    following = generate_direction_question(signs, Random(0), question.repeat_key)
    assert following is not None
    assert following.repeat_key != question.repeat_key
