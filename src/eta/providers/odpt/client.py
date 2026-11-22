import os
import asyncio
from typing import Any, Self

import httpx
from pydantic import BaseModel

from eta import config

ENV_FILE_NAME = "odpt.env"
ACCESS_TOKEN_ENV = "ODPT_ACCESS_TOKEN"

BASE_URL = "https://api.odpt.org/api/v4"

ACCESS_TOKEN_PARAM = "acl:consumerKey"
ACCESS_TOKEN_MASK = "ACCESS_TOKEN_IS_MASKED"

MAX_CONCURRENT_REQUESTS = 1

def redact_access_token(request: httpx.Request) -> None:

    request.url = request.url.copy_set_param(ACCESS_TOKEN_PARAM, ACCESS_TOKEN_MASK)

class ODPTClient:

    def __init__(
            self: Self, 
            access_token: str | None = None, 
            base_url: str = BASE_URL,
            transport: httpx.AsyncBaseTransport | None = None,
        ) -> None:

        if not access_token:
            config.load_env(ENV_FILE_NAME)
            access_token = os.getenv(ACCESS_TOKEN_ENV)
        if not access_token:
            raise config.ConfigError(f"{ACCESS_TOKEN_ENV} not found")        

        self._client = httpx.AsyncClient(
                base_url = base_url,
                params = {ACCESS_TOKEN_PARAM: access_token},
                headers = {"Accept": "application/json"},
                transport = transport,
            )

        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def get(self: Self, rdf_type: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:

        try:
            async with self._semaphore:
                response = await self._client.get(f"./{rdf_type}", params=params)
        except httpx.RequestError as error:
            redact_access_token(error.request)
            raise

        redact_access_token(response.request)
        response.raise_for_status()

        body: list[dict[str, Any]] = response.json()

        return body

    async def build[M: BaseModel](self, model: type[M], rdf_type: str, params: dict[str, str] | None = None) -> list[M]:

        return [model.model_validate(item) for item in await self.get(rdf_type, params)]

    async def aclose(self: Self) -> None:

        await self._client.aclose()
