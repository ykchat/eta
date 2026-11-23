import asyncio
from contextlib import AsyncExitStack, aclosing, closing
from collections.abc import Callable, Awaitable
from typing import Self, Concatenate

from eta.providers.base import Provider
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.provider import ODPTJSONProvider
from eta.storage.base import StaticDB
from eta.storage.sqlite import SQLiteStaticDB

class AppContext:

    def __init__(self: Self, stack: AsyncExitStack) -> None:

        self._stack = stack
        self._provider: Provider | None = None
        self._static_db: StaticDB | None = None

    async def provider(self: Self) -> Provider:

        if self._provider is None:
            client = await self._stack.enter_async_context(aclosing(ODPTClient()))
            self._provider = ODPTJSONProvider(client)

        return self._provider

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
