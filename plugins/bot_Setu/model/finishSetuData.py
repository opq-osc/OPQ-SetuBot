from pydantic import BaseModel


class FinishSetuData(BaseModel):
    title: str = ""
    picID: str = ""
    picWebUrl: str = ""
    page: str = ""
    author: str = ""
    authorID: str = ""
    authorWebUrl: str = ""
    picOriginalUrl: str = ""
    picLargeUrl: str = ""
    picMediumUrl: str = ""
    picOriginalUrl_Msg: str = ""
    tags: str = ""
