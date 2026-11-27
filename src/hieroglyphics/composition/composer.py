"""Build quadrats from ordered signs without crossing word boundaries."""

from collections.abc import Iterable

from hieroglyphics.composition.quadrat import Axis, Composition, Group, Node, Sign
from hieroglyphics.composition.sign_layout import Proportion, sign_layout

_PAIR_AXES = {
    Proportion.WIDE: Axis.VERTICAL,
    Proportion.TALL: Axis.HORIZONTAL,
    Proportion.COMPACT: Axis.HORIZONTAL,
}


def _compose_word(glyphs: str) -> tuple[Node, ...]:
    """
    Group a word from left to right in logical order.

    :param glyphs: Ordered glyphs in one word.
    :return: Ordered quadrats in that word.
    """
    signs = tuple(Sign(glyph) for glyph in glyphs)
    proportions = tuple(sign_layout(sign.glyph).proportion for sign in signs)
    quadrats: list[Node] = []
    index = 0

    while index < len(signs):
        first = signs[index]
        proportion = proportions[index]
        # Two compact signs fit below a wide sign or beside a tall sign.
        # Consume the whole group in place so its reading order is retained.
        if proportions[index + 1:index + 3] == (Proportion.COMPACT,) * 2:
            if proportion in (Proportion.WIDE, Proportion.TALL):
                axis = _PAIR_AXES[proportion]
                inner_axis = Axis.HORIZONTAL if axis is Axis.VERTICAL else Axis.VERTICAL
                pair = Group(inner_axis, signs[index + 1:index + 3])
                quadrats.append(Group(axis, (first, pair)))
                index += 3
                continue

        axis = _PAIR_AXES.get(proportion)
        if axis is not None and proportions[index + 1:index + 2] == (proportion,):
            quadrats.append(Group(axis, signs[index:index + 2]))
            index += 2
        else:
            quadrats.append(first)
            index += 1

    return tuple(quadrats)


def compose(words: Iterable[str]) -> Composition:
    """
    Compose each nonempty run of signs independently.

    :param words: Ordered glyph strings, one per source word.
    :return: Composition in logical reading order.
    """
    return Composition(tuple(_compose_word(word) for word in words if word))
