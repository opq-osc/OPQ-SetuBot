import asyncio
import re
from typing import Union

from botoy import S, ctx, mark_recv, logger, Action, jconfig

from .command import CMD
from .database import getFriendConfig, getGroupConfig, getRevokeTime, buildConfig
from .model import GetSetuConfig
from .setu import Setu

setuPattern = "来(.*?)[点丶、个份张幅](.*?)的?([rR]18)?[色瑟涩䔼😍🐍][图圖🤮]"
digitalConversionDict = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


async def check_and_processing(ctx, msg, info, user_config) -> Union[GetSetuConfig, None]:
    S_ = S.bind(ctx)
    getSetuConfig = GetSetuConfig()
    if ctx.group_msg:  # 群聊
        getSetuConfig.QQG = msg.from_group
    else:
        if not msg.is_private:  # 好友
            getSetuConfig.QQG = 0
        else:  # 私聊
            getSetuConfig.QQG = msg.from_group
    getSetuConfig.botqq = msg.bot_qq
    getSetuConfig.QQ = msg.from_user
    getSetuConfig.msgtype = {1: "friend", 2: "group", 3: "temp"}[msg.from_type.value]
    # print(info[1], info[2], info[3])
    if info[1] != "":
        if info[1] in digitalConversionDict.keys():
            getSetuConfig.toGetNum = int(digitalConversionDict[info[1]])
        else:
            if info[1].isdigit():
                getSetuConfig.toGetNum = int(info[1])
            else:
                await S_.text(user_config.replyMsg.inputError)
                # logger.info('非数字')
                return None
    else:  # 未指定数量,默认1
        getSetuConfig.toGetNum = 1
    getSetuConfig.tags = [i for i in set(re.split(r"[,， ]", info[2])) if i != ""]
    if info[3]:  # r18关键字
        getSetuConfig.level = 1
    return getSetuConfig


async def main():
    if m := (ctx.group_msg or ctx.friend_msg):
        # if m.bot_qq != jconfig.qq:  # 只接收一个bot
        #     return
        if m.text in ["色图", "setu"]:
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if not await getGroupConfig(m.from_group) and jconfig.get("setuconfig.autobuild"):
                    await buildConfig(m.bot_qq, m.from_group)

                if config := await getGroupConfig(m.from_group):
                    await Setu(ctx, GetSetuConfig(botqq=m.bot_qq, QQG=m.from_group, QQ=m.from_user,
                                                  msgtype={1: "friend", 2: "group", 3: "temp"}[m.from_type.value]),
                               config).group_or_temp()

                else:
                    logger.warning("无群:{}的配置文件".format(m.from_group))
                    return
            else:
                if config := await getFriendConfig():
                    await Setu(ctx, GetSetuConfig(botqq=m.bot_qq, QQG=0, QQ=m.from_user,
                                                  msgtype={1: "friend", 2: "group", 3: "temp"}[m.from_type.value]),
                               config).friend()
        elif info := m.text_match(setuPattern):
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if not await getGroupConfig(m.from_group) and jconfig.get("setuconfig.autobuild"):
                    await buildConfig(m.bot_qq, m.from_group)

                if config := await getGroupConfig(m.from_group):
                    if getSetuConfig := await check_and_processing(ctx, m, info, config):
                        await Setu(ctx, getSetuConfig, config).group_or_temp()

                else:
                    logger.warning("无群:{}的配置文件".format(m.from_group))
                    return

            else:  # from_type == 1
                if config := await getFriendConfig():
                    if getSetuConfig := await check_and_processing(ctx, m, info, config):
                        await Setu(ctx, getSetuConfig, config).friend()

                else:
                    logger.warning("无好友的配置文件(0.json)")
                    return


async def setu_revoke():
    if m := ctx.group_msg:
        # if m.bot_qq != jconfig.qq:
        #     return
        # if not m.is_from_self:
        #     return
        if not m.images:
            return
        await asyncio.sleep(3)  # 等opq返回msgseq
        if delay := await getRevokeTime(botqq=m.bot_qq, group=m.from_group, msgseq=m.msg_seq):
            await asyncio.sleep(delay)
            logger.success(
                f"撤回bot:{m.bot_qq} 群[{m.from_group_name}:{m.from_group}] [msg_seq:{m.msg_seq} msg_random:{m.msg_random}]")
            await Action(qq=m.bot_qq).revoke(m)


async def buildconfig():
    if m := (ctx.group_msg or ctx.friend_msg):
        if m.from_user == jconfig.get("setuconfig.admin"):
            action = Action(qq=m.bot_qq)
            if m.text == "生成配置文件":
                if await getGroupConfig(m.from_group):
                    logger.warning(f"群:{m.from_group}的配置文件已存在")
                    await S.text(f"群:{m.from_group}的配置文件已存在")
                    return
                else:
                    await buildConfig(m.bot_qq, m.from_group)
                    await S.text(f"群:{m.from_group}\r\nsetu配置文件创建成功")
            elif info := re.match("生成配置文件 ?(\d+)", m.text):
                groupid = info[1]
                if await getGroupConfig(groupid):
                    logger.warning(f"群:{groupid}的配置文件已存在")
                    await S.text("配置文件已存在")
                    return
                if int(groupid) not in [_["GroupCode"] for _ in await action.getGroupList()]:
                    await S.text(f"不存在群:{groupid}")
                    return
                await buildConfig(m.bot_qq, groupid)
                await S.text(f"群:{groupid}\r\nsetu配置文件创建成功")


async def setu_cmd():
    if m := (ctx.group_msg or ctx.friend_msg):
        if m.text[:4] == "_cmd":
            if m.from_user == jconfig.get("setuconfig.admin"):
                if res := re.match(r"_cmd [G,g] (\d+) (.*)", m.text):  # 提取群号
                    groupid = int(res[1])
                    cmd_text = res[2]
                elif res := re.match("_cmd (.*)", m.text):  # 匹配命令
                    if m.from_type.value in [2, 3]:
                        cmd_text = res[1]
                        groupid = m.from_group
                    else:
                        S.text("无法获取群号")
                        return
                else:
                    S.text("无权限")
                    return
                await CMD(S.bind(ctx), groupid, cmd_text).main()

            elif m.from_type.value in [2, 3]:
                if config := await getGroupConfig(m.from_group):
                    if m.from_user in config["admins"]:
                        await CMD(S.bind(ctx), m.from_group).main()
                    else:
                        S.text("无权限")


mark_recv(main, author='yuban10703', name="发送色图", usage='来张色图')
mark_recv(setu_revoke, author='yuban10703', name="撤回色图", usage='None')
mark_recv(buildconfig, author='yuban10703', name="生成setu配置文件", usage='发送"生成配置文件"')
mark_recv(setu_cmd, author='yuban10703', name="修改setu配置文件", usage='发送"_cmd"')
