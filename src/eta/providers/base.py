from typing import Self, Protocol

from eta.models import Operator

class Provider(Protocol):

    async def get_operators(self: Self) -> list[Operator]: ...