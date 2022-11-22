from enum import IntEnum


class TextDirection(IntEnum):
    LEFT_TO_RIGHT = 0
    RIGHT_TO_LEFT = 1

    @staticmethod
    def get_descriptions():
        return ["left to right", "right to left"]

    @staticmethod
    def get_direction_description(direction):
        return TextDirection.get_descriptions()[direction]
