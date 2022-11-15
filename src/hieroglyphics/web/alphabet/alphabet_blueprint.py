from flask import Blueprint, render_template
from hieroglyphics.transliteration import get_alphabet, get_transliterations

alphabet_bp = Blueprint("alphabet", __name__, template_folder='templates')


@alphabet_bp.route("/", methods=["GET"])
def alphabet():
    """
    Serve the page to prompt for a word or

    :return: The rendered page template
    """
    transliteration_table = get_transliterations("alphabet")
    letters, transliteration = get_alphabet(transliteration_table)
    return render_template("alphabet/alphabet.html",
                           letters=letters,
                           transliteration=transliteration)
