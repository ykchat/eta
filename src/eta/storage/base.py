from typing import Self, Protocol

from eta.models import Operator

class StaticDB(Protocol):

    def get_operators(self: Self) -> list[Operator]: ...

    def save_operators(self: Self, source_id: str, operators: list[Operator]) -> None: ...