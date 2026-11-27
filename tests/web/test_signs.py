from pathlib import Path

import pytest

from hieroglyphics.catalogue.signs import DATA_DIRECTORY, generate_catalogue, get_catalogue
from hieroglyphics.web import create_app


_REFERENCE_DATA = Path(__file__).resolve().parents[2] / "data"


def test_catalogue_is_reproducible(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Regenerate the packaged catalogue and log selection and transfer.

    :param tmp_path: Directory for the regenerated output.
    :param caplog: Captured catalogue generation messages.
    """
    output = tmp_path / "signs.json"
    with caplog.at_level("INFO"):
        generate_catalogue(
            _REFERENCE_DATA / "catalogue-content.txt",
            _REFERENCE_DATA / "Unikemet.txt",
            output,
        )
    assert output.read_bytes() == (DATA_DIRECTORY / "signs.json").read_bytes()
    assert "Selected M18 (U+131CD)" in caplog.text
    assert "Transferring M18 (U+131CD)" in caplog.text


def test_catalogue_rejects_incomplete_selection(tmp_path: Path) -> None:
    """
    Report required signs omitted from the selection before replacing output.

    :param tmp_path: Directory for the incomplete list and prior output.
    """
    selection = tmp_path / "incomplete.txt"
    selection.write_text("M18\n", encoding="utf-8")
    output = tmp_path / "signs.json"
    output.write_bytes(b"existing output")

    with pytest.raises(ValueError, match="missing required signs") as error:
        generate_catalogue(selection, _REFERENCE_DATA / "Unikemet.txt", output)
    assert "G17 (U+13153, letter M, position 1)" in str(error.value)
    assert "S29 (U+132F4, letter X, position 2)" in str(error.value)
    assert output.read_bytes() == b"existing output"


@pytest.mark.parametrize(
    ("parameters", "expected"),
    [
        ({"q": "g17"}, {0x13153}),
        ({"q": "OWL"}, {0x13153}),
        ({"q": "13153"}, {0x13153}),
        ({"q": "U+13153"}, {0x13153}),
        ({"q": chr(0x13153)}, {0x13153}),
        ({"q": "rw"}, {0x130ED}),
        ({"q": "s"}, {0x13283, 0x132F4}),
        ({"consonants": "2", "function": "Phonemogram"}, {0x130ED, 0x1336F}),
        ({"group": "E", "q": "rw"}, {0x130ED}),
        ({"group": "G", "q": "rw"}, set()),
    ],
)
def test_sign_search(parameters: dict[str, str], expected: set[int]) -> None:
    """Search and facets select the expected sign cards."""
    with create_app().test_client() as client:
        response = client.get("/signs/", query_string=parameters)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count('class="sign-card"') == len(expected)
    for scalar in expected:
        assert f'class="sign-card" href="/signs/U+{scalar:05X}"' in html
    if not expected:
        assert "No signs match" in html


def test_catalogue_detail_and_links(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catalogue entries link from the alphabet and both result directions."""
    monkeypatch.delenv("HIEROGLYPHICS_DATA", raising=False)
    with create_app().test_client() as client:
        assert len(get_catalogue()[1]) == 36
        assert client.get("/signs/").get_data(as_text=True).count('class="sign-card"') == 36
        detail = client.get("/signs/U+132F4").get_data(as_text=True)
        assert "S29" in detail and "folded piece of cloth" in detail
        assert "X (2 times)" in detail and "UniKemet 18.0.0" in detail
        assert client.get("/signs/U+13000").status_code == 200
        assert client.get("/signs/U+13001").status_code == 404
        assert client.get("/signs/U+wrong").status_code == 404
        licence = client.get("/signs/licence")
        assert licence.status_code == 200
        assert licence.mimetype == "text/plain"
        assert licence.get_data(as_text=True) == (
            _REFERENCE_DATA / "Unikemet-LICENSE.txt"
        ).read_text(encoding="utf-8")
        assert client.get("/alphabet/").get_data(as_text=True).count('href="/signs/U+132F4"') == 4
        for direction in (0, 1):
            response = client.post("/transliterate/", data={"word": "X", "direction": direction})
            assert response.get_data(as_text=True).count('href="/signs/U+132F4"') == 2


def test_custom_sign_without_catalogue_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep custom glyphs visible even when they cannot link to a catalogue entry."""
    from hieroglyphics.transliteration import transliterator

    (tmp_path / "alphabet_l_to_r.csv").write_text("Letter,Code 1,Code 2\nA,13001,132F4\n", encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_DATA", str(tmp_path))
    monkeypatch.setattr(transliterator, "_transliteration_tables", {})
    with create_app().test_client() as client:
        alphabet = client.get("/alphabet/").get_data(as_text=True)
        response = client.post("/transliterate/", data={"word": "A", "direction": 0})

    for html in (alphabet, response.get_data(as_text=True)):
        assert chr(0x13001) in html
        assert 'href="/signs/U+13001"' not in html
        assert 'href="/signs/U+132F4"' in html
