from copy import deepcopy
from flask import Blueprint, render_template, request
from hieroglyphics.transliteration import get_transliterations, transliterate
from hieroglyphics.web.transliterate import TextDirection
from hieroglyphics.web.logging_wrapper import log_message

transliterate_bp = Blueprint("transliterate", __name__, template_folder='templates')


def _render_page(word, transliterated, transliteration, direction, error):
    """
    Helper to render the transliteration page

    :param word: Original word
    :param transliterated: Word that was transliterated, excluding characters that have no equivalent
    :param transliteration: Transliteration of the word to hieroglyphics
    :param direction: Text direction for rendering hieroglyphs
    :param error: Error message to display on the page or None
    :return: The rendered page template
    """
    return render_template("transliterate/transliterate.html",
                           word=word,
                           direction=direction,
                           letters=transliterated,
                           transliteration=transliteration,
                           error=error)


@transliterate_bp.route("/", methods=["GET", "POST"])
def transliterate_word():
    """
    Serve the page to prompt for a word or

    :return: The rendered page template
    """
    if request.method == "POST":
        # Set defaults (which will be overwritten with values from the request data)
        direction = TextDirection.LEFT_TO_RIGHT
        word = ""

        try:
            # Get the text direction from the request data
            direction = int(request.form["direction"])
            direction_description = TextDirection.get_direction_description(direction)
            log_message("transliterate_word", f"Text direction is {direction_description}")

            # Get the word and deep copy it as we may need to reverse it, depending on the text direction,
            # and doing so directly on the request changes the request data. We also preserve the original
            # to repopulate the form when the page is rendered
            word = request.form["word"]
            word_to_transliterate = deepcopy(word)
            if direction == TextDirection.RIGHT_TO_LEFT:
                word_to_transliterate = word_to_transliterate[::-1]
            log_message("transliterate_word", f"Word is {word_to_transliterate}")

            # Perform the transliteration
            transliteration_table = get_transliterations("alphabet_l_to_r")
            transliterated, transliteration = transliterate(transliteration_table, word_to_transliterate)
            return _render_page(word, transliterated, transliteration, direction, None)

        except BaseException as e:
            return _render_page(word, "", "", direction, e)
    else:
        return _render_page("", "", "", TextDirection.LEFT_TO_RIGHT, None)
