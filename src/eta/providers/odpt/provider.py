from typing import Self, Iterable

from eta import config
from eta.models import Operator
from eta.providers.odpt.client import ODPTClient
from eta.schemas.odpt import ODPTOperator
from eta.schemas.gtfs_jp import GTFSAgency
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
   
class ODPTGTFSProvider:

    def __init__(self: Self, client: ODPTClient, feeds: list[ODPTGTFSFeed] | None = None) -> None:

        if feeds is None:
            feeds = ODPTGTFSFeeds.model_validate(config.load_toml(GTFS_FEEDS_FILE_NAME)).feeds

        self._client = client
        self._feeds = feeds

    async def get_operators(self: Self) -> list[Operator]:

        operators: list[Operator] = []
        for feed in self._feeds:
            files = await self._client.get_files(feed.operator, feed.name, feed.date, ["agency.txt"])
            agency = GTFSAgency.model_validate(files["agency.txt"][0])
            operators.append(ODPTGTFSProvider.build_operator(feed, agency))

        return operators

    @classmethod
    def build_operator(cls: type[Self], feed: ODPTGTFSFeed, agency: GTFSAgency) -> Operator:

        return Operator(id=feed.id(), name=feed.operator, titles={"ja": agency.agency_name})
