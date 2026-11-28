from typing import Self

from eta import config
from eta.models import Operator, Stop
from eta.providers.odpt.client import ODPTClient
from eta.schemas.odpt import ODPTOperator
from eta.schemas.gtfs_jp import GTFSTranslation, GTFSAgency, GTFSStop
from eta.schemas.feeds import ODPTGTFSFeed, ODPTGTFSFeeds

GTFS_FEEDS_FILE_NAME = "odpt_gtfs.toml"

class ODPTJSONProvider:

    def __init__(self: Self, client: ODPTClient) -> None:

        self._client = client

    async def get_operators(self: Self) -> list[Operator]:

        operators = await self._client.build(ODPTOperator, "odpt:Operator")

        return [ODPTJSONProvider.build_operator(operator) for operator in operators]

    @classmethod
    def build_operator(cls: type[Self], operator: ODPTOperator) -> Operator:

        titles = dict(operator.titles or {})

        if operator.title:
            titles.setdefault("ja", operator.title)

        return Operator(id=operator.id, name=operator.name(), titles=titles)

    async def get_stops(self: Self) -> list[Stop]:

        raise NotImplementedError("odpt_json does not support stops yet")

class ODPTGTFSProvider:

    def __init__(self: Self, client: ODPTClient, feeds: list[ODPTGTFSFeed] | None = None) -> None:

        if feeds is None:
            feeds = ODPTGTFSFeeds.model_validate(config.load_toml(GTFS_FEEDS_FILE_NAME)).feeds

        self._client = client
        self._feeds = feeds

    async def get_operators(self: Self) -> list[Operator]:

        operators: list[Operator] = []
        for feed in self._feeds:
            target_file_names = ["agency.txt"]
            files = await self._client.get_files(feed.operator, feed.name, feed.date, target_file_names)
            agency = GTFSAgency.model_validate(files["agency.txt"][0])
            operators.append(ODPTGTFSProvider.build_operator(agency))

        return operators

    @classmethod
    def build_operator(cls: type[Self], agency: GTFSAgency) -> Operator:

        return Operator(id=agency.id(), name=agency.agency_name, titles={"ja": agency.agency_name})

    async def get_stops(self: Self) -> list[Stop]:

        stops: list[Stop] = []
        for feed in self._feeds:
            target_file_names = ["translations.txt", "agency.txt", "stops.txt"]
            files = await self._client.get_files(feed.operator, feed.name, feed.date, target_file_names)
            agency = GTFSAgency.model_validate(files["agency.txt"][0])
            gtfs_stops = [GTFSStop.model_validate(row) for row in files["stops.txt"]]
            translations = [GTFSTranslation.model_validate(row) for row in files.get("translations.txt", [])]
            stops.extend(ODPTGTFSProvider.build_stops(agency, gtfs_stops, translations))

        return stops

    @classmethod
    def build_stops(cls: type[Self], agency: GTFSAgency, gtfs_stops: list[GTFSStop], translations: list[GTFSTranslation]) -> list[Stop]:

        titles_by_stop_name: dict[str, dict[str, str]] = {}
        for translation in translations:
            if translation.table_name == "stops" and translation.field_name == "stop_name":
                titles = titles_by_stop_name.setdefault(translation.field_value, {})
                titles[translation.language] = translation.translation

        gtfs_stops_by_id = {gtfs_stop.stop_id: gtfs_stop for gtfs_stop in gtfs_stops}

        stops: list[Stop] = []
        for gtfs_stop in gtfs_stops:

            parent_id = None
            if gtfs_stop.parent_station != "":
                parent_id = gtfs_stops_by_id[gtfs_stop.parent_station].id(agency)

            platform = None
            if gtfs_stop.platform_code != "":
                platform = gtfs_stop.platform_code

            stops.append(Stop(
                id = gtfs_stop.id(agency),
                name = gtfs_stop.name(agency),
                operator_id = agency.id(),
                titles = {"ja": gtfs_stop.stop_name} | titles_by_stop_name.get(gtfs_stop.stop_name, {}),
                parent_id = parent_id,
                platform = platform,
            ))

        return stops