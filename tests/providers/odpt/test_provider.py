from pathlib import Path
from contextlib import aclosing

import httpx
import pytest

from tests import helper
from eta.errors import ConfigError
from eta.models import Operator, Stop
from eta.schemas.odpt import ODPTOperator
from eta.schemas.gtfs_jp import GTFSTranslation, GTFSAgency, GTFSStop
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.provider import ODPTJSONProvider
from eta.providers.odpt.provider import ODPTGTFSProvider
from eta.schemas.feeds import ODPTGTFSFeed

pytestmark = pytest.mark.anyio

RINKO_FEED = ODPTGTFSFeed(operator="KawasakiTsurumiRinkoBus", name="allrinko", date="20261101")
RINKO_AGENCY = (
        "agency_id,agency_name\n"
        "5020001072478,川崎鶴見臨港バス株式会社\n"
    )
RINKO_STOPS = (
        "stop_id,stop_name,location_type,parent_station,platform_code\n"
        "10,川崎駅前,1,,\n"
        "10_1,川崎駅前,0,10,1\n"
    )
RINKO_TRANSLATIONS = (
        "table_name,field_name,language,translation,field_value\n"
        "stops,stop_name,en,Kawasaki Sta.,川崎駅前\n"
    )
RINKO_OPERATOR =  Operator(
        id = "gtfs.Operator:川崎鶴見臨港バス株式会社",
        name = "川崎鶴見臨港バス株式会社",
        titles = {"ja": "川崎鶴見臨港バス株式会社"},
    )
RINKO_KAWASAKI_STATION = Stop(
        id="gtfs.BusstopPole:川崎鶴見臨港バス株式会社.川崎駅前.10",
        name="川崎鶴見臨港バス株式会社.川崎駅前.10",
        operator_id="gtfs.Operator:川崎鶴見臨港バス株式会社",
        titles={"ja": "川崎駅前", "en": "Kawasaki Sta."},
    )
RINKO_KAWASAKI_PLATFORM = Stop(
        id="gtfs.BusstopPole:川崎鶴見臨港バス株式会社.川崎駅前.10.1",
        name="川崎鶴見臨港バス株式会社.川崎駅前.10.1",
        operator_id="gtfs.Operator:川崎鶴見臨港バス株式会社",
        titles={"ja": "川崎駅前", "en": "Kawasaki Sta."},
        parent_id="gtfs.BusstopPole:川崎鶴見臨港バス株式会社.川崎駅前.10",
        platform="1",
    )

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

    agency = GTFSAgency.model_validate({
            "agency_id": "5020001072478",
            "agency_name": "川崎鶴見臨港バス株式会社",
            "agency_url": "https://www.rinkobus.co.jp/",
        })

    assert ODPTGTFSProvider.build_operator(agency) == RINKO_OPERATOR

async def test_get_operators_from_gtfs() -> None:

    content = helper.make_zip({"agency.txt": RINKO_AGENCY})

    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content))) as client:
        operators = await ODPTGTFSProvider(client, [RINKO_FEED]).get_operators()

    assert len(operators) == 1

    assert operators[0] == RINKO_OPERATOR

def test_build_stops_from_gtfs() -> None:

    translations = [
        GTFSTranslation.model_validate({
                "table_name": "stops",
                "field_name": "stop_name",
                "language": "en",
                "translation": "Kawasaki Sta.",
                "field_value": "川崎駅前",
            }),
        GTFSTranslation.model_validate({
                "table_name": "stop_times",
                "field_name": "stop_headsign",
                "language": "en",
                "translation": "KAWASAKI STA.",
                "field_value": "川崎駅前",
            }),
    ]

    agency = GTFSAgency.model_validate({
            "agency_id": "5020001072478",
            "agency_name": "川崎鶴見臨港バス株式会社",
        })

    gtfs_stops = [
        GTFSStop.model_validate({
                "stop_id": "10",
                "stop_name": "川崎駅前",
                "location_type": "1"}
            ),
        GTFSStop.model_validate({
                "stop_id": "10_1",
                "stop_name": "川崎駅前",
                "location_type": "0",
                "parent_station": "10",
                "platform_code": "1",
            }),
    ]

    stops = ODPTGTFSProvider.build_stops(agency, gtfs_stops, translations)

    assert len(stops) == 2
    assert stops[0] == RINKO_KAWASAKI_STATION
    assert stops[1] == RINKO_KAWASAKI_PLATFORM

async def test_get_stops_from_gtfs() -> None:

    content = helper.make_zip({
            "agency.txt": RINKO_AGENCY,
            "stops.txt": RINKO_STOPS,
            "translations.txt": RINKO_TRANSLATIONS,
        })

    async with aclosing(ODPTClient("dummy", transport=helper.mock(body=content))) as client:
        stops = await ODPTGTFSProvider(client, [RINKO_FEED]).get_stops()

    assert len(stops) == 2
    assert stops[0] == RINKO_KAWASAKI_STATION
    assert stops[1] == RINKO_KAWASAKI_PLATFORM

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