from pydantic import BaseModel, ConfigDict

class GTFSModel(BaseModel):

    model_config = ConfigDict(extra="allow", frozen=True)

# 事業者 agency.txt
class GTFSAgency(GTFSModel):

    agency_id: str = ""
    agency_name: str