from typing import Self

from eta.models import Operator
from eta.providers.base import Provider
from eta.providers.odpt.client import ODPTClient
from eta.providers.odpt.models import ODPTOperator

class ODPTProvider(Provider):

    def __init__(self: Self, client: ODPTClient) -> None:

        self._client = client

    async def get_operators(self: Self) -> list[Operator]:

        operators = await self._client.build(ODPTOperator, "odpt:Operator")

        return [operator.build() for operator in operators] 

    