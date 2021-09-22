from tinydb import where
from tinyrecord import transaction

from ._share import gachaDB
from ..model import UserInfo


def getUserConfig(userid: int, cardPool: str) -> UserInfo:
    with transaction(gachaDB.table(cardPool)) as tr:
        with tr.lock:
            if res := gachaDB.table(cardPool).get(where('userid') == userid):
                return UserInfo(**res)
            else:  # 生成新配置文件
                return UserInfo(userid=userid)


def updateUserConfig(userid: int, cardPool: str, config: UserInfo) -> bool:
    with transaction(gachaDB.table(cardPool)) as tr:
        with tr.lock:
            if gachaDB.table(cardPool).get(where('userid') == userid):
                tr.table(cardPool).update(config.dict(), where('userid') == userid)
                return True
            else:
                tr.insert(config.dict())
                return True
