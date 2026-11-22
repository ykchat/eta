from pathlib import Path
from contextlib import aclosing

import httpx
import pytest

from eta.config import ConfigError
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.models import ODPTOperator

pytestmark = pytest.mark.anyio

OPERATORS = [{"owl:sameAs": "odpt.Operator:Toei", "dc:title": "東京都交通局"}]

def mock(status: int = 200, body: object = OPERATORS, urls: list[httpx.URL] | None = None) -> httpx.MockTransport:

    def respond(request: httpx.Request) -> httpx.Response:
        if urls is not None:
            urls.append(request.url)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(respond)

async def test_build_models() -> None:

    async with aclosing(ODPTClient("dummy", transport=mock())) as client:
        (operator,) = await client.build(ODPTOperator, "odpt:Operator")

    assert operator.id == "odpt.Operator:Toei"

async def test_request_url() -> None:

    urls: list[httpx.URL] = []
    async with aclosing(ODPTClient("SECRET", transport=mock(urls=urls))) as client:
        await client.get("odpt:BusstopPole", {"dc:title": "新宿駅西口"})

    url = urls[0]
    assert url.path == "/api/v4/odpt:BusstopPole"
    assert url.params["dc:title"] == "新宿駅西口"
    assert url.params["acl:consumerKey"] == "SECRET"

async def test_access_token_is_masked_on_error() -> None:

    async with aclosing(ODPTClient("SECRET", transport=mock(429))) as client:
        with pytest.raises(httpx.HTTPStatusError) as error:
            await client.get("odpt:Operator")

    assert "SECRET" not in str(error.value)
    assert "SECRET" not in str(error.value.request.url)

async def test_access_token_is_masked_on_connection_error() -> None:

    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("接続できません", request=request)

    async with aclosing(ODPTClient("SECRET", transport=httpx.MockTransport(fail))) as client:
        with pytest.raises(httpx.ConnectError) as error:
            await client.get("odpt:Operator")

    assert "SECRET" not in str(error.value.request.url)

def clear_access_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("ODPT_ACCESS_TOKEN", "")
    monkeypatch.delenv("ODPT_ACCESS_TOKEN")
    monkeypatch.chdir(tmp_path)

def test_missing_access_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    clear_access_token(tmp_path, monkeypatch)

    with pytest.raises(ConfigError):
        ODPTClient()

async def test_access_token_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    clear_access_token(tmp_path, monkeypatch)

    env_dir = tmp_path / ".secrets"
    env_dir.mkdir()
    env_file = env_dir / "odpt.env"
    env_file.write_text("ODPT_ACCESS_TOKEN=FROM_FILE\n")

    urls: list[httpx.URL] = []
    async with aclosing(ODPTClient(transport=mock(urls=urls))) as client:
        await client.get("odpt:Operator")

    assert urls[0].params["acl:consumerKey"] == "FROM_FILE"