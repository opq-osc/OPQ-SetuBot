from pathlib import Path

import ujson as json
from botoy import logger, contrib, Action

from ..model import GroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径


@contrib.to_async
def writeData(path, admins):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            GroupConfig(admins=admins).dict(), f, indent=4, ensure_ascii=False
        )


async def buildConfig(botqq, groupid):
    action = Action(qq=botqq)
    file_path = curFileDir / "DB" / "configs" / f"{groupid}.json"
    adminList = await action.getGroupAdminList(groupid)
    admins_QQid = [i["Uin"] for i in adminList]
    await writeData(file_path, admins_QQid)
    logger.success(f"{groupid}.json创建成功")
