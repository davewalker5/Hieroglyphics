from src.hieroglyphics.web.transliterate import TextDirection


def test_can_get_l_to_r_description():
    description = TextDirection.get_direction_description(TextDirection.LEFT_TO_RIGHT).casefold()
    assert "left to right" == description


def test_can_get_r_to_l_description():
    description = TextDirection.get_direction_description(TextDirection.RIGHT_TO_LEFT).casefold()
    assert "right to left" == description
