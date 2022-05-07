import re
from pathlib import Path
from typing import Union

import ujson as json
from botoy import Action, FriendMsg, GroupMsg, S
from botoy import decorators as deco
from botoy import jconfig, logger

from .groupConfig import GroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径
configDir = curFileDir.parent / "bot_Setu" / "database" / "DB" / "configs"


def writeData(path, admins):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            GroupConfig(admins=admins).dict(), f, indent=4, ensure_ascii=False
        )


@deco.from_these_users(jconfig.superAdmin, jconfig.qq)  # 只接受bot自己和bot管理员的消息
@deco.startswith("生成配置文件")
@deco.need_action
def main(ctx: Union[FriendMsg, GroupMsg], action: Action):
    if ctx.type == "group":
        file_path = configDir / f"{ctx.QQG}.json"
        if file_path.is_file():
            logger.warning(f"群:{ctx.QQG}的配置文件已存在")
            S.text(f"群:{ctx.QQG}的配置文件已存在")
            return
        else:
            adminList = action.getGroupAdminList(ctx.QQG)
            admins_QQid = [i["MemberUin"] for i in adminList]
            writeData(file_path, admins_QQid)
            logger.success(f"{ctx.QQG}.json创建成功")
            S.text(f"群:{ctx.QQG}\r\nsetu配置文件创建成功")
    else:
        if info := re.match("生成配置文件 ?(\d+)", ctx.Content):
            groupid = info[1]
            file_path = configDir / f"{groupid}.json"
            if file_path.is_file():
                logger.warning(f"群:{groupid}的配置文件已存在")
                S.text("配置文件已存在")
                return
            if int(groupid) not in [_["GroupId"] for _ in action.getGroupList()]:
                S.text(f"不存在群:{groupid}")
                return
            adminList = action.getGroupAdminList(int(groupid))
            admins_QQid = [i["MemberUin"] for i in adminList]
            writeData(file_path, admins_QQid)
            logger.success(f"{groupid}.json创建成功")
            S.text(f"群:{groupid}\r\nsetu配置文件创建成功")


def receive_group_msg(ctx):
    main(ctx)


def receive_friend_msg(ctx):
    main(ctx)
