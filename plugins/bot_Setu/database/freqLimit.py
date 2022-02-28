import time

from botoy import logger
from botoy.contrib import to_async
from tinydb import where
from tinydb.operations import add
from tinyrecord import transaction

from ._shared import freqLimitTable
from ..model import getSetuConfig


@to_async
def freqLimit(groupid, config, get_setu_config: getSetuConfig):
    """
    频率限制
    :return:
    """
    with transaction(freqLimitTable) as tr:
        with tr.lock:
            if data_tmp := freqLimitTable.get(where("group") == groupid):  # 如果有数据
                # print(data_tmp)
                freqConfig = config.setting.freq
                if freqConfig.refreshTime != 0 and (
                        time.time() - data_tmp["time"] >= freqConfig.refreshTime
                ):  # 刷新
                    tr.update(
                        {"time": time.time(), "callDone": 0}, where("group") == groupid
                    )
                    return False
                elif (
                        freqConfig.limitCount != 0
                        and (get_setu_config.toGetNum + data_tmp["callDone"]) > freqConfig.limitCount
                ):
                    # 大于限制且不为0
                    logger.info(
                        "群:{}大于频率限制:{}次/{}s".format(
                            groupid, freqConfig.limitCount, freqConfig.refreshTime
                        )
                    )
                    return freqConfig, data_tmp
                # 记录
                tr.update(
                    add("callDone", get_setu_config.toGetNum), where("group") == groupid
                )
                return False
            else:  # 没数据
                logger.info("群:{}第一次调用".format(groupid))
                tr.insert(
                    {"group": groupid, "time": time.time(), "callDone": get_setu_config.toGetNum}
                )
            return False
