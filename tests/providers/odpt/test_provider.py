from pathlib import Path
from contextlib import aclosing

import httpx
import pytest

from tests import helper
from eta.errors import ConfigError
from eta.models import Operator
from eta.schemas.odpt import ODPTOperator
from eta.schemas.gtfs_jp import GTFSAgency
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.provider import ODPTJSONProvider
from eta.providers.odpt.provider import ODPTGTFSProvider
from eta.schemas.feeds import ODPTGTFSFeed

pytestmark = pytest.mark.anyio

RINKO_FEED = ODPTGTFSFeed(operator="KawasakiTsurumiRinkoBus", name="allrinko", date="20261101")
RINKO_AGENCY = "agency_id,agency_name\n5020001072478,川崎鶴見臨港バス株式会社\n"

def test_build_operator_with_titles_from_odpt() -> None:

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

def test_build_operator_without_titles_from_odpt() -> None:

    odpt = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Rinko", 
            "dc:title": "川崎鶴見臨港バス"
        })

    operator = ODPTJSONProvider.build_operator(odpt) 

    assert operator.title("ja") == "川崎鶴見臨港バス"
    assert operator.title("en") is None

def test_build_operator_without_any_title_from_odpt() -> None:

    odpt = ODPTOperator.model_validate({"owl:sameAs": "odpt.Operator:Unknown"})

    assert ODPTJSONProvider.build_operator(odpt).titles == {}

def test_build_operator_from_gtfs() -> None:

    feed = ODPTGTFSFeed(operator="KawasakiTsurumiRinkoBus", name="allrinko", date="20261101")

    agency = GTFSAgency.model_validate({
            "agency_id": "5020001072478",
            "agency_name": "川崎鶴見臨港バス株式会社",
            "agency_url": "https://www.rinkobus.co.jp/",
        })

    assert ODPTGTFSProvider.build_operator(feed, agency) == Operator(
            id = "odpt.Operator:KawasakiTsurumiRinkoBus",
            name = "KawasakiTsurumiRinkoBus",
            titles = {"ja": "川崎鶴見臨港バス株式会社"},
        )

async def test_get_operators_from_gtfs() -> None:

    content = helper.make_zip({"agency.txt": RINKO_AGENCY})

    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content))) as client:
        operators = await ODPTGTFSProvider(client, [RINKO_FEED]).get_operators()

    assert operators == [Operator(
            id="odpt.Operator:KawasakiTsurumiRinkoBus",
            name="KawasakiTsurumiRinkoBus",
            titles={"ja": "川崎鶴見臨港バス株式会社"},
        )]

async def test_feeds_from_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.chdir(tmp_path)

    toml_dir = tmp_path / ".eta"
    toml_dir.mkdir()
    toml_file = toml_dir / "odpt_gtfs.toml"
    toml_file.write_text(
        '[[feeds]]\noperator = "KawasakiTsurumiRinkoBus"\nname = "allrinko"\ndate = "20261101"\n',
        encoding="utf-8",
    )

    content = helper.make_zip({"agency.txt": RINKO_AGENCY})

    urls: list[httpx.URL] = []
    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content, urls=urls))) as client:
        await ODPTGTFSProvider(client).get_operators()

    url = urls[0]
    assert url.path == "/api/v4/files/odpt/KawasakiTsurumiRinkoBus/allrinko.zip"

async def test_missing_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.chdir(tmp_path)

    async with aclosing(ODPTClient("dummy", transport=helper.mock())) as client:
        with pytest.raises(ConfigError):
            ODPTGTFSProvider(client)