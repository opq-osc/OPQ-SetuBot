from typing import List

from pydantic import BaseModel, Field


class GetSetuConfig(BaseModel):
    level: int = Field(0, ge=0, le=2)  # 0:非r18 1:r18 2:混合
    toGetNum: int = Field(1, ge=1)
    doneNum: int = 0
    # flagID: int = 0
    # ctx: Union[GroupMsg, FriendMsg]
    tags: List[str] = []
    # quality: Literal['original', 'large', 'medium'] = 'large'
    # proxy: bool
