import asyncio
from contextlib import AsyncExitStack, aclosing, closing
from collections.abc import Callable, Awaitable
from typing import Self, Concatenate

from eta.providers.base import Provider
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.provider import ODPTJSONProvider, ODPTGTFSProvider
from eta.storage.base import StaticDB
from eta.storage.sqlite import SQLiteStaticDB

PROVIDERS: dict[str, Callable[[ODPTClient], Provider]] = {
    "odpt_json": ODPTJSONProvider,
    "odpt_gtfs": ODPTGTFSProvider,
}

class AppContext:

    def __init__(self: Self, stack: AsyncExitStack) -> None:

        self._stack = stack
        self._client: ODPTClient | None = None
        self._providers: dict[str, Provider] = {}
        self._static_db: StaticDB | None = None

    def source_ids(self: Self) -> list[str]:

        return list(PROVIDERS)

    async def provider(self: Self, source_id: str) -> Provider:

        if source_id not in self._providers:
            if self._client is None:
                self._client = await self._stack.enter_async_context(aclosing(ODPTClient()))
            self._providers[source_id] = PROVIDERS[source_id](self._client)

        return self._providers[source_id]

    def static_db(self: Self) -> StaticDB:

        if self._static_db is None:
            self._static_db = SQLiteStaticDB()
            self._stack.enter_context(closing(self._static_db.connection()))
            self._stack.enter_context(self._static_db.connection())

        return self._static_db

def call[**P, T](
        func: Callable[Concatenate[AppContext, P], Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:

    async def call_with_context() -> T:
        async with AsyncExitStack() as stack:
            context = AppContext(stack)
            return await func(context, *args, **kwargs)

    return asyncio.run(call_with_context())
