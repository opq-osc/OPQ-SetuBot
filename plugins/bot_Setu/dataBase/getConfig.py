import time
from pathlib import Path
from typing import Union

import ujson as json
from loguru import logger

from ..model import FriendConfig, GroupConfig

curFileDir = Path(__file__).absolute().parent  # 当前文件路径


def getGroupConfig(groupID) -> Union[GroupConfig, None]:
    path = curFileDir / "DB" / "configs" / "{}.json".format(groupID)  # 拼接路径
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GroupConfig(**data)
        except Exception as e:
            logger.error("请检查{}.json文件\r\n{}".format(groupID, e))
            return None
    else:
        # logger.warning('无群配置文件')
        return None


def getFriendConfig() -> Union[FriendConfig, None]:
    path = curFileDir / "DB" / "configs" / "{}.json".format(0)  # 拼接路径
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return FriendConfig(**data)
        except Exception as e:
            logger.error("请检查{}.json文件\r\n{}".format(0, e))
            return None
    else:
        # logger.warning('无群配置文件')
        return None
