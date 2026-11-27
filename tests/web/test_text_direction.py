import re

import pytest

from hieroglyphics.web import create_app
from hieroglyphics.web.transliterate import TextDirection


def test_can_get_l_to_r_description():
    description = TextDirection.get_direction_description(TextDirection.LEFT_TO_RIGHT).casefold()
    assert "left to right" == description


def test_can_get_r_to_l_description():
    description = TextDirection.get_direction_description(TextDirection.RIGHT_TO_LEFT).casefold()
    assert "right to left" == description


@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize(
    ("direction", "direction_class", "letters", "code_points"),
    [
        (0, "l-to-r", ["A", "x", "B"], [(0x1313F,), (0x132F4, 0x132F4), (0x130C0,)]),
        (1, "r-to-l", ["B", "x", "A"], [(0x130C0,), (0x132F4, 0x132F4), (0x1313F,)]),
    ],
)
def test_transliteration_direction(
    preview: bool,
    direction: int,
    direction_class: str,
    letters: list[str],
    code_points: list[tuple[int, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Check sign order, repetition and orientation in both response formats.

    :param preview: Whether to request the live result fragment.
    :param direction: Reading direction submitted by the user.
    :param direction_class: Expected suffix of the glyph orientation class.
    :param letters: Expected order of source letters.
    :param code_points: Expected Unicode sequences for the glyphs.
    :param monkeypatch: Fixture used to select the packaged transliteration data.
    """
    monkeypatch.delenv("HIEROGLYPHICS_DATA", raising=False)
    with create_app().test_client() as client:
        url = "/transliterate/?preview=1" if preview else "/transliterate/"
        response = client.post(url, data={"word": "A x!B", "direction": direction})

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert ('id="transliteration-form"' in html) == (not preview)
    assert re.findall(r'<td class="letter-cell">([^<]+)</td>', html) == letters
    glyphs = re.findall(rf'<td class="hieroglyph-cell-{direction_class}">(.*?)</td>', html, re.S)
    assert [tuple(map(ord, re.sub(r"<[^>]+>", "", glyph))) for glyph in glyphs] == code_points
