from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

# 取得元
class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    operator_count: int = 0
    updated_at: datetime | None = None

# 事業者
class Operator(BaseModel):

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    titles: dict[str, str] = Field(default_factory=dict)

    def title(self: Self, locale: str) -> str | None:

        return self.titles.get(locale)