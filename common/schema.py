from enum import Enum, auto
from typing import Any, List


class SeparatorStyle(Enum):
    SINGLE = "###"
    TWO = "</s>"
    THREE = auto()
    FOUR = auto()
