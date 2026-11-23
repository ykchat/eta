from pydantic import BaseModel, ConfigDict

class ODPTGTFSFeed(BaseModel):

    model_config = ConfigDict(frozen=True)

    operator: str
    name: str
    date: str
    
    def id(self) -> str:

        return f"odpt.Operator:{self.operator}"


class ODPTGTFSFeeds(BaseModel):

    feeds: list[ODPTGTFSFeed] = []