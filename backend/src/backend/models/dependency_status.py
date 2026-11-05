from enum import StrEnum
from enum import auto
from typing import final


# Whether a dependency of the backend can currently be used.
@final
class DependencyStatus(StrEnum):
    UP = auto()
    DOWN = auto()
