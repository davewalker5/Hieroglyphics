"""Represent quadrats as signs and groups in logical reading order."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Axis(Enum):
    """Direction along which a group's children are read."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class Sign:
    """A single hieroglyph in a composition."""

    glyph: str

    def __post_init__(self) -> None:
        """
        Ensure a sign contains one character.

        :raises ValueError: If the glyph is empty or contains several characters.
        """
        if len(self.glyph) != 1:
            raise ValueError("A sign must contain exactly one character")


@dataclass(frozen=True)
class Group:
    """A horizontal or vertical arrangement in logical reading order."""

    axis: Axis
    children: tuple[Sign | Group, ...]

    def __post_init__(self) -> None:
        """
        Validate the group structure.

        :raises ValueError: If the arrangement axis or child count is invalid.
        """
        if not isinstance(self.axis, Axis) or len(self.children) < 2:
            raise ValueError("A group needs a valid axis and at least two children")


Node = Sign | Group


@dataclass(frozen=True)
class Composition:
    """Words in logical order, each containing its ordered quadrats."""

    words: tuple[tuple[Node, ...], ...]
