"""Test quadrat rendering through the live transliteration endpoint."""

import re

import pytest

from hieroglyphics.web import create_app

PREVIEW_URL = "/transliterate/?preview=1"


@pytest.mark.parametrize("direction", [0, 1])
def test_switch_layouts(direction: int) -> None:
    """
    Switch layouts while keeping direction, word boundaries and sign order.

    :param direction: Text direction submitted with each layout.
    """
    with create_app().test_client() as client:
        form = {"word": "nn x! 👋", "direction": direction}
        quadrat_response = client.post(PREVIEW_URL, data=dict(form, layout="quadrat"))
        linear_response = client.post(PREVIEW_URL, data=dict(form, layout="linear"))

    quadrats = quadrat_response.get_data(as_text=True)
    linear = linear_response.get_data(as_text=True)

    direction_attribute = "rtl" if direction else "ltr"
    assert f'class="quadrat-output" dir="{direction_attribute}"' in quadrats
    assert quadrats.count('class="quadrat-word"') == 2
    assert quadrats.count('class="quadrat"') == 2
    assert re.findall(r"<text [^>]+>(.*?)</text>", quadrats) == list("𓈖𓈖𓋴𓋴")
    assert ("scale(-1 1)" in quadrats) == bool(direction)
    assert 'class="glyph-result"' in linear
    assert 'class="quadrat-output"' not in linear


@pytest.mark.parametrize("word", ["", "123 !"])
def test_empty_quadrat_preview(word: str) -> None:
    """
    Leave the result empty when the input produces no signs.

    :param word: Empty or unrecognised input.
    """
    with create_app().test_client() as client:
        form = {"word": word, "direction": 0, "layout": "quadrat"}
        response = client.post(PREVIEW_URL, data=form)

    assert response.status_code == 200
    assert response.get_data(as_text=True).strip() == ""


def test_invalid_layout() -> None:
    """Show a clear error for an unknown layout option."""
    with create_app().test_client() as client:
        response = client.post(PREVIEW_URL, data={"word": "a", "direction": 0, "layout": "invalid"})

    assert "Choose a valid layout mode." in response.get_data(as_text=True)
