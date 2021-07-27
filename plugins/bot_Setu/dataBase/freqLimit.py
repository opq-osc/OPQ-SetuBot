import time

from loguru import logger
from tinydb import where
from tinydb.operations import add

from ._shared import tmpDB


def freqLimit(groupid, config, getSetuConfig):
    """
    频率限制
    :return:
    """
    if data_tmp := tmpDB.table("freqLimit").get(where("group") == groupid):  # 如果有数据
        # print(data_tmp)
        freqConfig = config.setting.freq
        if freqConfig.refreshTime != 0 and (
            time.time() - data_tmp["time"] >= freqConfig.refreshTime
        ):  # 刷新
            tmpDB.table("freqLimit").update(
                {"time": time.time(), "callDone": 0}, where("group") == groupid
            )
            return False
        elif (
            freqConfig.limitCount != 0
            and (getSetuConfig.toGetNum + data_tmp["callDone"]) > freqConfig.limitCount
        ):
            # 大于限制且不为0
            logger.info(
                "群:{}大于频率限制:{}次/{}s".format(
                    groupid, freqConfig.limitCount, freqConfig.refreshTime
                )
            )
            return freqConfig, data_tmp
        # 记录
        tmpDB.table("freqLimit").update(
            add("callDone", getSetuConfig.toGetNum), where("group") == groupid
        )
        return False
    else:  # 没数据
        logger.info("群:{}第一次调用".format(groupid))
        tmpDB.table("freqLimit").insert(
            {"group": groupid, "time": time.time(), "callDone": getSetuConfig.toGetNum}
        )
    return False
