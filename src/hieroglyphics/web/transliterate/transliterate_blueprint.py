from flask import Blueprint, render_template, request

from hieroglyphics.transliteration import get_transliterations, transliterate
from hieroglyphics.web.transliterate import TextDirection

transliterate_bp = Blueprint("transliterate", __name__, template_folder="templates")


@transliterate_bp.route("/", methods=["GET", "POST"])
def transliterate_word() -> str:
    """
    Render the transliteration workspace or its live result fragment.

    :return: Rendered workspace or result fragment HTML.
    """
    word = request.form.get("word", "")
    direction = TextDirection.LEFT_TO_RIGHT
    letters: list[str] = []
    glyphs: list[str] = []
    error = None

    if request.method == "POST":
        try:
            direction = TextDirection(int(request.form["direction"]))
        except (KeyError, ValueError):
            error = "Choose a valid text direction."
        else:
            if word:
                source = word[::-1] if direction == TextDirection.RIGHT_TO_LEFT else word
                table = get_transliterations("alphabet_l_to_r")
                letters, glyphs = transliterate(table, source)

    template = "transliterate/transliterate.html"
    if request.method == "POST" and request.args.get("preview") == "1":
        template = "transliterate/result.html"

    return render_template(
        template,
        word=word,
        direction=direction,
        letters=letters,
        transliteration=glyphs,
        error=error,
    )
