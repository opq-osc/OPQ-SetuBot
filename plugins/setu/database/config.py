from pathlib import Path
from typing import Union

import ujson as json
from botoy import logger, contrib, Action

from ..model import FriendConfig, GroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径


@contrib.to_async
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


@contrib.to_async
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


async def buildConfig(botqq, groupid):
    action = Action(qq=botqq)
    admins_QQid = [i["Uin"] for i in await action.getGroupAdminList(groupid)]
    await updateGroupConfig(groupid, GroupConfig(admins=admins_QQid).dict())
    # logger.success(f"{groupid}.json创建成功")


@contrib.to_async
def updateGroupConfig(groupid, config):
    try:
        data = GroupConfig(**config).dict()
    except Exception as e:
        logger.error("数据类型检查错误\r\n%s" % e)
        return False
    try:
        with open(
                curFileDir
                / "DB"
                / "configs"
                / "{}.json".format(groupid),
                "w",
                encoding="utf-8",
        ) as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("写入{}.json成功".format(groupid))
        return True
    except Exception as e:
        logger.error("写入{}.json失败\r\n{}".format(groupid, e))
        return False
