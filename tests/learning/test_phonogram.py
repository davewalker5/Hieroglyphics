"""Verify that phonogram classification applies to individual readings."""

from random import Random

from hieroglyphics.catalogue.signs import Sign
from hieroglyphics.learning.phonogram import generate_phonogram_question


def test_classifies_each_validated_reading() -> None:
    """Support readings of different lengths and normalise combining marks."""
    sign = Sign(0x13193, {"kEH_Func": "Phonemogram", "kEH_FVal": "d\u0331 | wn | nfr"})
    expected = {"ḏ": "UNILITERAL", "wn": "BILITERAL", "nfr": "TRILITERAL"}
    randomizer = Random(42)
    seen = {}
    for _ in range(30):
        question = generate_phonogram_question([sign], randomizer, sign.code_point)
        assert question is not None
        assert question.repeat_key == sign.code_point
        choices = {choice.identifier for choice in question.choices}
        assert choices == set(expected.values())
        assert question.consonants == tuple(question.reading)
        seen[question.reading] = question.correct.identifier
    assert seen == expected


def test_excludes_ambiguous_or_undocumented_readings() -> None:
    """Require an explicit phonogram use and unqualified consonant symbols."""
    signs = [
        Sign(0x13124, {"kEH_FVal": "nfr"}),
        Sign(0x131CD, {"kEH_Func": "Phonemogram/logogram", "kEH_FVal": "ꞽy"}),
        Sign(0x131AC, {"kEH_Func": "Logogram", "kEH_FVal": "ꜥnḫ"}),
        Sign(0x133D4, {"kEH_Func": "Phonemogram", "kEH_FVal": "t | sn?"}),
    ]
    assert generate_phonogram_question(signs, Random(42)) is None


def test_prefers_a_different_sign() -> None:
    """Skip an immediately repeated glyph when another glyph can be used."""
    hare = Sign(0x130F9, {"kEH_Func": "Phonemogram", "kEH_FVal": "wn"})
    heart = Sign(0x13124, {"kEH_Func": "Phonemogram", "kEH_FVal": "nfr"})
    question = generate_phonogram_question([hare, heart], Random(42), hare.code_point)
    assert question is not None
    assert question.sign == heart
