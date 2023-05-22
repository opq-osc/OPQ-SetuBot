import re
from pathlib import Path

import ujson as json
from botoy import S, ctx, mark_recv, Action
from botoy import jconfig, logger,contrib

from .groupConfig import GroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径
configDir = curFileDir.parent / "setu" / "database" / "DB" / "configs"

@contrib.to_async
def writeData(path, admins):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            GroupConfig(admins=admins).dict(), f, indent=4, ensure_ascii=False
        )


async def main():
    if m := (ctx.group_msg or ctx.friend_msg):
        if m.from_user == jconfig.get("setuconfig.admin"):
            action = Action(qq=m.bot_qq)
            if m.text == "生成配置文件":
                file_path = configDir / f"{m.from_group}.json"
                if file_path.is_file():
                    logger.warning(f"群:{m.from_group}的配置文件已存在")
                    await S.text(f"群:{m.from_group}的配置文件已存在")
                    return
                else:
                    adminList = await action.getGroupAdminList(m.from_group)
                    admins_QQid = [i["Uin"] for i in adminList]
                    await writeData(file_path, admins_QQid)
                    logger.success(f"{m.from_group}.json创建成功")
                    await S.text(f"群:{m.from_group}\r\nsetu配置文件创建成功")
            elif info := re.match("生成配置文件 ?(\d+)", m.text):
                groupid = info[1]
                file_path = configDir / f"{groupid}.json"
                if file_path.is_file():
                    logger.warning(f"群:{groupid}的配置文件已存在")
                    await S.text("配置文件已存在")
                    return
                if int(groupid) not in [_["GroupCode"] for _ in await action.getGroupList()]:
                    await S.text(f"不存在群:{groupid}")
                    return
                adminList = await action.getGroupAdminList(int(groupid))
                admins_QQid = [i["Uin"] for i in adminList]
                await writeData(file_path, admins_QQid)
                logger.success(f"{groupid}.json创建成功")
                await S.text(f"群:{groupid}\r\nsetu配置文件创建成功")


mark_recv(main, author='yuban10703', name="生成setu配置文件", usage='发送"生成配置文件"')
