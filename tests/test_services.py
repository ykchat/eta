from typing import Self

import pytest

from eta import services, errors
from eta.models import Operator

pytestmark = pytest.mark.anyio

TOEI = Operator(
        id="odpt.Operator:Toei", 
        name="Toei", 
        titles={"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"}
    )
RINKO = Operator(
        id="odpt.Operator:Rinko", 
        name="Rinko", 
        titles={"ja": "川崎鶴見臨港バス"}
    )

class FakeProvider:

    def __init__(self: Self, operators: list[Operator]) -> None:

        self._operators = operators

    async def get_operators(self: Self) -> list[Operator]:

        return self._operators

class FakeStaticDB:

    def __init__(self: Self, operators_by_source: dict[str, list[Operator]] | None = None) -> None:

        self.operators_by_source = operators_by_source or {}

    def get_operators(self: Self) -> list[Operator]:

        operators: list[Operator] = []
        for operators_from_source in self.operators_by_source.values():
            operators.extend(operators_from_source)

        return operators

    def save_operators(self: Self, source_id: str, operators: list[Operator]) -> None:

        self.operators_by_source[source_id] = operators

class FakeContext:

    def __init__(self: Self, operators: dict[str, list[Operator]] | None = None) -> None:

        self._providers = {"odpt_json": FakeProvider([TOEI]), "odpt_gtfs": FakeProvider([RINKO])}
        self._static_db = FakeStaticDB(operators)

    def source_ids(self: Self) -> list[str]:

        return list(self._providers)

    async def provider(self: Self, source_id: str) -> FakeProvider:

        return self._providers[source_id]

    def static_db(self: Self) -> FakeStaticDB:

        return self._static_db

async def test_update_operators() -> None:

    context = FakeContext()

    operators = await services.update_operators(context)

    assert operators == [TOEI, RINKO]
    assert context.static_db().operators_by_source == {"odpt_json": [TOEI], "odpt_gtfs": [RINKO]}

async def test_update_operators_from_source() -> None:

    context = FakeContext({"odpt_json": [], "odpt_gtfs": []})

    operators = await services.update_operators(context, "odpt_gtfs")

    assert operators == [RINKO]
    assert context.static_db().operators_by_source == {"odpt_json": [], "odpt_gtfs": [RINKO]}

async def test_update_operators_of_unknown_source() -> None:

    with pytest.raises(errors.SourceNotFoundError):
        await services.update_operators(FakeContext(), "unknown")

async def test_get_all_operators() -> None:

    context = FakeContext({"odpt_json": [TOEI], "odpt_gtfs": [RINKO]})

    assert await services.get_operators(context, None) == [TOEI, RINKO]

@pytest.mark.parametrize(("query", "expected"), [
    ("臨港", [RINKO]),            # 日本語名
    ("rinko", [RINKO]),           # 名前(大文字・小文字は区別しない)
    ("BUREAU", [TOEI]),           # 英語名
    ("交通", [TOEI]),             # 日本語名
    ("新宿", []),                 # 一致なし
])
async def test_get_operators_by_query(query: str, expected: list[Operator]) -> None:

    context = FakeContext({"odpt_json": [TOEI], "odpt_gtfs": [RINKO]})

    assert await services.get_operators(context, query) == expected