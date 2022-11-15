import pytest
from hieroglyphics.transliteration import get_transliterations, transliterate, get_alphabet


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
