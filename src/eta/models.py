from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

# 取得元
class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    operator_count: int = 0
    updated_at: datetime | None = None

# 名前を言語ごとに持つモデル
class TitledModel(BaseModel):

    model_config = ConfigDict(frozen=True)

    titles: dict[str, str] = Field(default_factory=dict)

    def title(self: Self, locale: str) -> str | None:

        return self.titles.get(locale)

# 事業者
class Operator(TitledModel):

    model_config = ConfigDict(frozen=True)

    id: str
    name: str

# 停留所
class Stop(TitledModel):

    id: str
    name: str
    operator_id: str
    parent_id: str | None = None    # 属するまとまり
    platform: str | None = None     # のりば番号
