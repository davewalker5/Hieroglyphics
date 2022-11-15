from flask import Blueprint, render_template, request
from hieroglyphics.transliteration import get_transliterations, transliterate

transliterate_bp = Blueprint("transliterate", __name__, template_folder='templates')


def _render_page(word, transliterated, transliteration, error):
    """
    Helper to render the transliteration page

    :param word: Original word
    :param transliterated: Word that was transliterated, excluding characters that have no equivalent
    :param transliteration: Transliteration of the word to hieroglyphics
    :param error: Error message to display on the page or None
    :return: The rendered page template
    """
    return render_template("transliterate/transliterate.html",
                           word=word,
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
        try:
            word = request.form["word"]
            transliteration_table = get_transliterations("alphabet")
            transliterated, transliteration = transliterate(transliteration_table, word)
            return _render_page(word, transliterated, transliteration, None)
        except BaseException as e:
            return _render_page(word, "", "", e)
    else:
        return _render_page("", "", "", None)
