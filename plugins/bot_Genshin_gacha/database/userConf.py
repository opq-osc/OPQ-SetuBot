from tinydb import where

from ._share import gachaDB
from ..model import UserInfo


def getUserConfig(userid: int, cardPool: str) -> UserInfo:
    if res := gachaDB.table(cardPool).get(where('userid') == userid):
        return UserInfo(**res)
    else:  # 生成新配置文件
        return UserInfo(userid=userid)


def updateUserConfig(userid: int, cardPool: str, config: UserInfo) -> bool:
    if gachaDB.table(cardPool).get(where('userid') == userid):
        gachaDB.table(cardPool).update(config.dict(), where('userid') == userid)
        return True
    else:
        gachaDB.table(cardPool).insert(config.dict())
        return True
    # return False

