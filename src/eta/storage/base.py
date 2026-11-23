from typing import Self, Protocol

from eta.models import Source, Operator

class StaticDB(Protocol):

    def get_sources(self: Self) -> list[Source]: ...

    def get_operators(self: Self) -> list[Operator]: ...

    def save_operators(self: Self, source_id: str, operators: list[Operator]) -> None: ...