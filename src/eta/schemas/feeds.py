from pydantic import BaseModel, ConfigDict

class ODPTGTFSFeed(BaseModel):

    model_config = ConfigDict(frozen=True)

    operator: str
    name: str
    date: str

class ODPTGTFSFeeds(BaseModel):

    feeds: list[ODPTGTFSFeed] = []