import os
import asyncio
import io
import csv
import zipfile
from typing import Self, Any, Iterable

import httpx
from pydantic import BaseModel

from eta import config, errors

ENV_FILE_NAME = "odpt.env"
ACCESS_TOKEN_ENV = "ODPT_ACCESS_TOKEN"

BASE_URL = "https://api.odpt.org/api/v4"

ACCESS_TOKEN_PARAM = "acl:consumerKey"
ACCESS_TOKEN_MASK = "ACCESS_TOKEN_IS_MASKED"

TIMEOUT = 30
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
            raise errors.ConfigError(f"{ACCESS_TOKEN_ENV} not found")

        self._client = httpx.AsyncClient(
                base_url = base_url,
                params = {ACCESS_TOKEN_PARAM: access_token},
                follow_redirects = True,
                timeout = TIMEOUT,
                transport = transport,
            )

        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def get(self, path: str, params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> httpx.Response:

        try:
            async with self._semaphore:
                response = await self._client.get(f"./{path}", params=params, headers=headers)
        except httpx.RequestError as error:
            redact_access_token(error.request)
            raise

        redact_access_token(response.request)
        response.raise_for_status()

        return response

    async def get_json(self: Self, rdf_type: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:

        headers = {"Accept": "application/json"}

        response = await self.get(rdf_type, params, headers)

        return response.json()

    async def get_files(self, operator: str, name: str, date: str, target_file_names: Iterable[str]) -> dict[str, list[dict[str, str]]]:

        response = await self.get(f"files/odpt/{operator}/{name}.zip", {"date": date})

        content =  response.content

        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:

            file_names = set(zip_file.namelist())

            files: dict[str, list[dict[str, str]]] = {}
            for target_file_name in target_file_names:
                if target_file_name in file_names:
                    text = zip_file.read(target_file_name).decode("utf-8-sig")
                    files[target_file_name] = list(csv.DictReader(io.StringIO(text)))

            return files


    async def build[M: BaseModel](self, model: type[M], rdf_type: str, params: dict[str, str] | None = None) -> list[M]:

        return [model.model_validate(item) for item in await self.get_json(rdf_type, params)]

    async def aclose(self: Self) -> None:

        await self._client.aclose()
