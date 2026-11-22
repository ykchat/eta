from typing import Self

from pydantic import BaseModel, ConfigDict, Field

# 事業者
class Operator(BaseModel):

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    titles: dict[str, str] = Field(default_factory=dict)

    def title(self: Self, locale: str) -> str | None:

        return self.titles.get(locale)