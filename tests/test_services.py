from typing import Self

import pytest

from eta import services
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

    async def get_operators(self: Self) -> list[Operator]:

        return [TOEI, RINKO]

class FakeStaticDB:

    def __init__(self: Self, operators: list[Operator] | None = None) -> None:

        self.operators = operators or []

    def get_operators(self: Self) -> list[Operator]:

        return self.operators

    def save_operators(self: Self, operators: list[Operator]) -> None:

        self.operators = operators

class FakeContext:

    def __init__(self: Self, operators: list[Operator] | None = None) -> None:

        self._provider = FakeProvider()
        self._static_db = FakeStaticDB(operators)

    async def provider(self: Self) -> FakeProvider:

        return self._provider

    def static_db(self: Self) -> FakeStaticDB:

        return self._static_db

async def test_update_operators() -> None:

    context = FakeContext()

    operators = await services.update_operators(context)

    assert operators == [TOEI, RINKO]
    assert context.static_db().operators == [TOEI, RINKO] 

async def test_get_all_operators() -> None:

    context = FakeContext([TOEI, RINKO])

    assert await services.get_operators(context, None) == [TOEI, RINKO]

@pytest.mark.parametrize(("query", "expected"), [
    ("臨港", [RINKO]),            # 日本語名
    ("rinko", [RINKO]),           # 名前(大文字・小文字は区別しない)
    ("BUREAU", [TOEI]),           # 英語名
    ("交通", [TOEI]),             # 日本語名
    ("新宿", []),                 # 一致なし
])
async def test_get_operators_by_query(query: str, expected: list[Operator]) -> None:

    context = FakeContext([TOEI, RINKO])

    assert await services.get_operators(context, query) == expected