from typing import Self, Protocol

from eta.providers.base import Provider
from eta.storage.base import StaticDB

class Context(Protocol):

    async def provider(self: Self) -> Provider: ...

    def static_db(self: Self) -> StaticDB: ...
