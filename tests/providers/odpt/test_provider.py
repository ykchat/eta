from pathlib import Path
from contextlib import aclosing

import httpx
import pytest

from tests import helper
from eta.config import ConfigError
from eta.models import Operator
from eta.schemas.odpt import ODPTOperator
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.provider import ODPTJSONProvider
from eta.providers.odpt.provider import ODPTGTFSProvider
from eta.schemas.feeds import ODPTGTFSFeed

pytestmark = pytest.mark.anyio

RINKO = ODPTGTFSFeed(operator="KawasakiTsurumiRinkoBus", name="allrinko", date="20261101")

def test_build_with_titles() -> None:

    odpt = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Toei",
            "dc:title": "東京都交通局",
            "odpt:operatorTitle": {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        })

    assert ODPTJSONProvider.build_operator(odpt) == Operator(
            id = "odpt.Operator:Toei",
            name = "Toei",
            titles = {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        )

def test_build_without_titles() -> None:

    odpt = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Rinko", 
            "dc:title": "川崎鶴見臨港バス"
        })

    operator = ODPTJSONProvider.build_operator(odpt) 

    assert operator.title("ja") == "川崎鶴見臨港バス"
    assert operator.title("en") is None

def test_build_without_any_title() -> None:

    odpt = ODPTOperator.model_validate({"owl:sameAs": "odpt.Operator:Unknown"})

    assert ODPTJSONProvider.build_operator(odpt).titles == {}


async def test_get_feeds() -> None:

    content = helper.make_zip({"agency.txt": "agency_id,agency_name\n5020001072478,川崎鶴見臨港バス株式会社\n"})

    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content))) as client:
        feeds = await ODPTGTFSProvider(client, ["agency.txt"], [RINKO]).get_feed_files()

    assert feeds == {"odpt.Operator:KawasakiTsurumiRinkoBus": {
        "agency.txt": "agency_id,agency_name\n5020001072478,川崎鶴見臨港バス株式会社\n",
    }}

async def test_feeds_from_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.chdir(tmp_path)

    toml_dir = tmp_path / ".eta"
    toml_dir.mkdir()
    toml_file = toml_dir / "odpt_gtfs.toml"
    toml_file.write_text(
        '[[feeds]]\noperator = "KawasakiTsurumiRinkoBus"\nname = "allrinko"\ndate = "20261101"\n',
        encoding="utf-8",
    )

    content = helper.make_zip({})

    urls: list[httpx.URL] = []
    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content, urls=urls))) as client:
        await ODPTGTFSProvider(client, ["agency.txt"]).get_feed_files()

    url = urls[0]
    assert url.path == "/api/v4/files/odpt/KawasakiTsurumiRinkoBus/allrinko.zip"

async def test_missing_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.chdir(tmp_path)

    async with aclosing(ODPTClient("dummy", transport=helper.mock())) as client:
        with pytest.raises(ConfigError):
            ODPTGTFSProvider(client, ["agency.txt"])