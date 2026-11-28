from typing import Self

from pydantic import BaseModel, ConfigDict

class GTFSModel(BaseModel):

    model_config = ConfigDict(extra="allow", frozen=True)

# 事業者 agency.txt
class GTFSAgency(GTFSModel):

    agency_id: str = ""
    agency_name: str

    def operator_id(self: Self) -> str:

        return f"gtfs.Operator:{self.agency_name}"