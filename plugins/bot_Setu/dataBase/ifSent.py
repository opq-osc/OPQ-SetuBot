import time

from tinydb import where

from ._shared import tmpDB


def ifSent(groupId: int, picId: int, refreshTime: int):
    if data := tmpDB.table("sentlist").get(where("group") == groupId):  # 如果有数据
        if sendTime := data["sent_dict"].get(picId):
            return True if time.time() - sendTime <= refreshTime else False
        else:  # 记录
            for k in list(data["sent_dict"].keys()):  # 清除过期数据
                if time.time() - data["sent_dict"][k] > refreshTime:
                    del data["sent_dict"][k]
            data["sent_dict"][picId] = time.time()
            tmpDB.table("sentlist").update(
                {"sent_dict": data["sent_dict"]}, where("group") == groupId
            )
            return False
    else:  # 没数据
        tmpDB.table("sentlist").insert(
            {"group": groupId, "sent_dict": {picId: time.time()}}
        )
        return False
