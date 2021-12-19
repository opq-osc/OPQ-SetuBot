import time

from botoy.contrib import to_async
from tinydb import where
from tinyrecord import transaction

from ._shared import sentlistTable


@to_async
def ifSent(groupId: int, picId: int, pic_page: int, refresh_time: int):
    with transaction(sentlistTable) as tr:
        with tr.lock:
            if data := sentlistTable.get(where("group") == groupId):  # 如果有数据
                if pic_send_info := data["sent_dict"].get(picId):
                    return True if time.time() - pic_send_info["time"] <= refresh_time else False
                else:
                    for k in list(data["sent_dict"].keys()):  # 清除过期数据
                        if time.time() - data["sent_dict"][k]["time"] > refresh_time:
                            del data["sent_dict"][k]
                    data["sent_dict"][picId] = {"time": time.time(), "page": pic_page}  # 记录
                    tr.update(
                        {"sent_dict": data["sent_dict"]}, where("group") == groupId
                    )
                    return False
            else:  # 没数据
                tr.insert(
                    {
                        "group": groupId,
                        "sent_dict": {
                            picId: {"time": time.time(), "page": pic_page}
                        }
                    }
                )
                return False
