from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from eta.models import Operator

class ODPTModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True, extra="allow", frozen=True)

    id: str = Field(alias="owl:sameAs")
    title: str | None = Field(default=None, alias="dc:title")

    def name(self: Self) -> str:

        return self.id.split(":", 1)[-1]

# 事業者 rdf:type = odpt:Operator
class ODPTOperator(ODPTModel):

    titles: dict[str, str] | None = Field(default=None, alias="odpt:operatorTitle")

    def build(self: Self) -> Operator:

        titles = dict(self.titles or {})

        if self.title:
            titles.setdefault("ja", self.title)

        return Operator(id=self.id, name=self.name(), titles=titles)
