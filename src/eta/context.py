from typing import Self, Protocol

from eta.providers.base import Provider
from eta.storage.base import StaticDB

class Context(Protocol):

    def source_ids(self: Self) -> list[str]: ...

    async def provider(self: Self, source_id: str) -> Provider: ...

    def static_db(self: Self) -> StaticDB: ...
