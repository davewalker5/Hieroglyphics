"""Browse and inspect the application's sign catalogue."""

from flask import Blueprint, Response, abort, render_template, request, send_file

from hieroglyphics.catalogue.signs import DATA_DIRECTORY, Sign, get_catalogue, group_label, search_signs
from hieroglyphics.transliteration import get_transliterations

signs_bp = Blueprint("signs", __name__, template_folder="templates")


@signs_bp.app_template_global()
def catalogue_sign(glyph: str) -> Sign | None:
    """
    Look up a single output glyph for use in a template.

    :param glyph: One Unicode character emitted by the transliterator.
    :return: The matching sign if included in the catalogue.
    """
    return get_catalogue()[1].get(ord(glyph))


@signs_bp.get("/")
def index() -> str:
    """
    Display the sign catalogue with the requested search and filters.

    :return: Rendered catalogue page.
    """
    version, signs = get_catalogue()
    query = request.args.get("q", "").strip()
    group = request.args.get("group", "")
    function = request.args.get("function", "")
    consonants = request.args.get("consonants", "")
    groups = sorted({sign.group for sign in signs.values() if sign.group})
    functions = sorted({sign.properties["kEH_Func"] for sign in signs.values() if sign.properties.get("kEH_Func")})
    return render_template(
        "signs/index.html",
        version=version,
        signs=search_signs(query, group, function, consonants),
        groups={code: group_label(code) for code in groups},
        functions=functions,
        query=query,
        group=group,
        function=function,
        consonants=consonants,
    )


@signs_bp.get("/<code_point>")
def detail(code_point: str) -> str:
    """
    Display one documented sign and its modern correspondences.

    :param code_point: Unicode code point in U+ hexadecimal notation.
    :return: Rendered sign detail page.
    """
    version, signs = get_catalogue()
    try:
        scalar = int(code_point[2:], 16) if code_point.upper().startswith("U+") else -1
    except ValueError:
        abort(404)

    sign = signs.get(scalar)
    if sign is None or code_point.upper() != sign.code_point:
        abort(404)

    return render_template(
        "signs/detail.html",
        sign=sign,
        version=version,
        classification=group_label(sign.group),
    )


@signs_bp.app_template_global()
def catalogue_letters(sign: Sign) -> list[tuple[str, int]]:
    """
    Find modern app correspondences that contain this sign.

    :param sign: Sign displayed in the catalogue entry.
    :return: App letters paired with the number of occurrences of the sign.
    """
    correspondences = get_transliterations("alphabet_l_to_r")
    return [
        (letter, sequence.count(sign.glyph))
        for letter, sequence in correspondences.items()
        if sign.glyph in sequence
    ]


@signs_bp.get("/licence")
def licence() -> Response:
    """
    Serve the Unicode copyright and permission notice for the catalogue.

    :return: Plain-text licence response.
    """
    return send_file(DATA_DIRECTORY / "Unikemet-LICENSE.txt", mimetype="text/plain")
