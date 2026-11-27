from flask import Blueprint, render_template

from hieroglyphics.catalogue.signs import get_catalogue, group_label
from hieroglyphics.transliteration import get_alphabet, get_transliterations

alphabet_bp = Blueprint("alphabet", __name__, template_folder='templates')


@alphabet_bp.route("/", methods=["GET"])
def alphabet():
    """
    Display the English letter correspondences and catalogue sources.

    :return: The rendered page template
    """
    transliteration_table = get_transliterations("alphabet_l_to_r")
    letters, transliteration = get_alphabet(transliteration_table)
    version, catalogue = get_catalogue()
    code_points = dict.fromkeys(ord(glyph) for sequence in transliteration for glyph in sequence)
    dialog_signs = [catalogue[code_point] for code_point in code_points if code_point in catalogue]
    return render_template("alphabet/alphabet.html",
                           letters=letters,
                           transliteration=transliteration,
                           version=version,
                           group_label=group_label,
                           dialog_signs=dialog_signs)
