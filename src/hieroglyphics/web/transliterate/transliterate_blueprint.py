from enum import Enum

from flask import Blueprint, render_template, request

from hieroglyphics.composition.composer import compose
from hieroglyphics.transliteration import get_transliterations, transliterate
from hieroglyphics.web.quadrat_renderer import QUADRAT_SIZE, render_quadrats
from hieroglyphics.web.transliterate.text_direction import TextDirection

transliterate_bp = Blueprint("transliterate", __name__, template_folder="templates")


class LayoutMode(Enum):
    """Available presentations of a transliteration."""

    LINEAR = "linear"
    QUADRAT = "quadrat"


@transliterate_bp.route("/", methods=["GET", "POST"])
def transliterate_word() -> str:
    """
    Render the transliteration workspace or its live result fragment.

    :return: Rendered workspace or result fragment HTML.
    """
    word = request.form.get("word", "")
    direction = TextDirection.LEFT_TO_RIGHT
    layout = LayoutMode.LINEAR
    letters: list[str] = []
    glyphs: list[str] = []
    drawings = ()
    error = None

    if request.method == "POST":
        try:
            direction = TextDirection(int(request.form["direction"]))
        except (KeyError, ValueError):
            error = "Choose a valid text direction."
        else:
            try:
                layout = LayoutMode(request.form.get("layout", LayoutMode.LINEAR.value))
            except ValueError:
                error = "Choose a valid layout mode."

    if request.method == "POST" and word and error is None:
        table = get_transliterations("alphabet_l_to_r")
        if layout is LayoutMode.QUADRAT:
            words = ("".join(transliterate(table, token)[1]) for token in word.split())
            drawings = render_quadrats(compose(words))
        else:
            letters, glyphs = transliterate(table, word)
            if direction == TextDirection.RIGHT_TO_LEFT:
                letters.reverse()
                glyphs.reverse()

    template = "transliterate/transliterate.html"
    if request.method == "POST" and request.args.get("preview") == "1":
        template = "transliterate/result.html"

    return render_template(
        template,
        word=word,
        direction=direction,
        layout=layout.value,
        letters=letters,
        transliteration=glyphs,
        drawings=drawings,
        quadrat_size=QUADRAT_SIZE,
        error=error,
    )
