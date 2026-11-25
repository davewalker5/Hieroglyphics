from hashlib import sha256
import json
from pathlib import Path

import pytest

from hieroglyphics.transliteration import get_alphabet, get_transliterations, load_transliterations, transliterate
from hieroglyphics.transliteration.unikemet import load_unikemet, validate_correspondences


@pytest.fixture()
def alphabet_l_to_r():
    return get_transliterations("alphabet_l_to_r")


@pytest.fixture()
def alphabet():
    return "abcdefghijklmnopqrstuvwxyz"


@pytest.fixture()
def sample_phrase():
    return "Ptolemy"


@pytest.fixture()
def sample_transliteration():
    return b'\xf0\x93\x8a\xaa\xf0\x93\x8f\x8f\xf0\x93\x8d\xaf\xf0\x93\x83\xad\xf0\x93\x87\x8b\xf0\x93\x85\x93\xf0\x93' \
           b'\x87\x8c'


def test_can_load_alphabet(alphabet_l_to_r):
    assert 26 == len(alphabet_l_to_r)


def test_table_has_all_letters(alphabet_l_to_r, alphabet):
    for letter in alphabet:
        transliterated, transliteration = transliterate(alphabet_l_to_r, letter)
        assert "" != transliterated
        assert "" != transliteration


def test_unicode_character_count(alphabet_l_to_r, alphabet):
    for letter in alphabet:
        _, transliteration = transliterate(alphabet_l_to_r, letter)
        # Converting to a byte array will give an array containing 4 bytes for each
        # unicode code point. The per-letter simplistic transliteration contains only
        # one code point per grapheme *except* for the hieroglyph for X, which has 2
        number_of_code_points = len(bytes("".join(transliteration), "utf-8")) / 4
        expected_code_points = 2 if letter == "x" else 1
        assert expected_code_points == number_of_code_points


def test_transliteration_of_sample_phrase(alphabet_l_to_r, sample_phrase, sample_transliteration):
    _, transliteration = transliterate(alphabet_l_to_r, sample_phrase)
    transliteration_bytes = bytes("".join(transliteration), "utf-8")
    assert len(sample_transliteration) == len(transliteration_bytes)

    for i in range(len(sample_transliteration)):
        assert sample_transliteration[i] == transliteration_bytes[i]


def test_invalidcharacter_gives_empty_result(alphabet_l_to_r):
    transliterated, transliteration = transliterate(alphabet_l_to_r, ".")
    assert 0 == len(transliterated)
    assert 0 == len(transliteration)


def test_can_get_alphabet(alphabet_l_to_r, alphabet):
    transliterated, transliteration = get_alphabet(alphabet_l_to_r)
    assert list(alphabet.upper()) == transliterated


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
DEFAULT_TABLE = PROJECT_ROOT / "src/hieroglyphics/transliteration/data/alphabet_l_to_r.csv"
EXPECTED_CODE_POINTS = (
    (0x1313F,), (0x130C0,), (0x132F4,), (0x130A7,), (0x131CB,), (0x13191,),
    (0x133BC,), (0x13254,), (0x131CB,), (0x13193,), (0x133A1,), (0x130ED,),
    (0x13153,), (0x13216,), (0x1336F,), (0x132AA,), (0x1320E,), (0x1308B,),
    (0x132F4,), (0x133CF,), (0x13171,), (0x13191,), (0x13171,),
    (0x132F4, 0x132F4), (0x131CC,), (0x13283,),
)


def test_default_correspondences_resolve_in_unikemet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check the vendor snapshot and validate the shipped CSV despite a local override."""
    monkeypatch.setenv("HIEROGLYPHICS_DATA", str(DATA_DIRECTORY / "unused"))
    snapshot = DATA_DIRECTORY / "Unikemet.txt"
    provenance = json.loads((DATA_DIRECTORY / "Unikemet-provenance.json").read_text(encoding="utf-8"))

    snapshot_bytes = snapshot.read_bytes()
    assert sha256(snapshot_bytes).hexdigest() == provenance["sha256"]
    assert snapshot_bytes.startswith(f"# Unikemet-{provenance['unicode_version']}.txt\n".encode())

    # An absolute path selects the packaged CSV independently of the configured directory.
    correspondences = load_transliterations(str(DEFAULT_TABLE))
    letters, output = get_alphabet(correspondences)
    assert letters == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert tuple(tuple(map(ord, sequence)) for sequence in output) == EXPECTED_CODE_POINTS
    validate_correspondences(correspondences, load_unikemet(snapshot))


def test_unikemet_validation_reports_missing_occurrences(tmp_path: Path) -> None:
    """Report both positions when a fixture repeats an unmatched scalar."""
    snapshot = tmp_path / "Unikemet.txt"
    snapshot.write_text(
        "# fixture\n\nU+13000\tkEH_Desc\t Seated man \nU+13000\tkEH_UniK\tA001\n",
        encoding="utf-8",
    )
    signs = load_unikemet(snapshot)
    assert signs == {0x13000: {"kEH_Desc": " Seated man ", "kEH_UniK": "A001"}}

    with pytest.raises(ValueError, match=r"'X' position 1: U\+132F4, 'X' position 2: U\+132F4"):
        validate_correspondences({"A": chr(0x13000), "X": chr(0x132F4) * 2}, signs)


def test_unikemet_rejects_duplicate_properties(tmp_path: Path) -> None:
    """Reject duplicate properties instead of replacing the earlier value."""
    snapshot = tmp_path / "Unikemet.txt"
    snapshot.write_text("U+13000\tkEH_Core\tC\nU+13000\tkEH_Core\tL\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r":2: duplicate kEH_Core for U\+13000"):
        load_unikemet(snapshot)


def test_custom_correspondence_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Preserve custom correspondences, including code points outside UniKemet."""
    (tmp_path / "custom.csv").write_text("Letter,Code 1\nA,0042\n", encoding="utf-8")
    monkeypatch.setenv("HIEROGLYPHICS_DATA", str(tmp_path))

    table = load_transliterations("custom.csv")
    assert transliterate(table, "a !") == (["a"], ["B"])
