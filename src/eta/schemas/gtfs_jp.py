from typing import Self

from pydantic import BaseModel, ConfigDict

class GTFSModel(BaseModel):

    model_config = ConfigDict(extra="allow", frozen=True)

# 翻訳 translations.txt
class GTFSTranslation(GTFSModel):

    table_name: str
    field_name: str
    language: str
    translation: str
    field_value: str = ""

# 事業者 agency.txt
class GTFSAgency(GTFSModel):

    agency_id: str = ""
    agency_name: str

    def id(self: Self) -> str:

        return f"gtfs.Operator:{self.agency_name}"

# 停留所・標柱 stops.txt
class GTFSStop(GTFSModel):

    stop_id: str
    stop_name: str
    location_type: str = ""  # 1: 停留所、0 or 空: 標柱
    parent_station: str = "" # 標標柱の場合は属する停留所の stop_id
    platform_code: str = ""  # のりば番号

    def name(self: Self, agency: GTFSAgency) -> str:

        return f"{agency.agency_name}.{self.stop_name}.{self.stop_id.replace('_', '.')}"

    def id(self: Self, agency: GTFSAgency) -> str:

        return f"gtfs.BusstopPole:{self.name(agency)}"

