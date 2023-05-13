import asyncio
import re
from typing import Union

from botoy import S, ctx, mark_recv, logger, Action, jconfig

from .model import GetSetuConfig
from .setu import Setu
from .database import freqLimit, getFriendConfig, getGroupConfig, ifSent, getRevokeTime
from .model import FinishSetuData, FriendConfig, GetSetuConfig, GroupConfig

__doc__ = "色图姬"

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
        if m.bot_qq != jconfig.qq:  # 只接收一个bot
            return
        if m.text in ["色图", "setu"]:
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if config := getGroupConfig(m.from_group):
                    await Setu(ctx, GetSetuConfig(QQG=m.from_group, QQ=m.from_user,
                                                  msgtype={1: "friend", 2: "group", 3: "temp"}[m.from_type.value]),
                               config).group_or_temp()
            else:
                if config := getFriendConfig():
                    await Setu(ctx, GetSetuConfig(QQG=0, QQ=m.from_user,
                                                  msgtype={1: "friend", 2: "group", 3: "temp"}[m.from_type.value]),
                               config).friend()
        elif info := m.text_match(setuPattern):
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if config := getGroupConfig(m.from_group):
                    if getSetuConfig := await check_and_processing(ctx, m, info, config):
                        await Setu(ctx, getSetuConfig, config).group_or_temp()

                else:
                    logger.warning("无群:{}的配置文件".format(m.from_group))
                    return

            else:  # from_type == 1
                if config := getFriendConfig():
                    if getSetuConfig := await check_and_processing(ctx, m, info, config):
                        await Setu(ctx, getSetuConfig, config).friend()

                else:
                    logger.warning("无好友的配置文件(0.json)")
                    return


async def setu_revoke():
    if m := ctx.group_msg:
        if m.bot_qq != jconfig.qq:
            return
        # if not m.is_from_self:
        #     return
        if not m.images:
            return
        if delay := await getRevokeTime(group=m.from_group, msgseq=m.msg_seq):
            await asyncio.sleep(delay)
            logger.info(f"撤回群[{m.from_group_name}:{m.from_group}] [msg_seq:{m.msg_seq} msg_random:{m.msg_random}]")
            await Action(qq=jconfig.qq, url=jconfig.url).revoke(m)


mark_recv(main, author='yuban10703', name="发送色图", usage='来张色图')
mark_recv(setu_revoke, author='yuban10703', name="撤回色图", usage='None')
