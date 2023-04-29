import asyncio
import re
from typing import Union

from botoy import S, ctx, mark_recv, logger

from .model import GetSetuConfig
from .setu import Setu
from .database import freqLimit, getFriendConfig, getGroupConfig, ifSent
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


async def check_and_processing(ctx, info, user_config) -> Union[GetSetuConfig, None]:
    S_ = S.bind(ctx)
    getSetuConfig = GetSetuConfig()
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
        if m.text in ["色图", "setu"]:
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if config := getGroupConfig(m.from_group):
                    ctx.QQG = m.from_group
                    ctx.QQ = m.from_user
                    ctx.type = "group" if m.from_type.value == 2 else "temp"
                    await Setu(ctx, GetSetuConfig(), config).group_or_temp()
            else:
                if config := getFriendConfig():
                    await Setu(ctx, GetSetuConfig(), config).friend()
        elif info := m.text_match(setuPattern):
            if m.from_type.value in [2, 3]:  # 群聊或者群临时会话就加载该群的配置文件
                if config := getGroupConfig(m.from_group):
                    ctx.QQG = m.from_group
                    ctx.QQ = m.from_user
                    ctx.type = "group" if m.from_type.value == 2 else "temp"
                    if getSetuConfig := await check_and_processing(ctx, info, config):
                        await Setu(ctx, getSetuConfig, config).group_or_temp()

                else:
                    logger.warning("无群:{}的配置文件".format(m.from_group))
                    return

            else:  # from_type == 1
                if config := getFriendConfig():
                    if getSetuConfig := await  check_and_processing(ctx, info, config):
                        await Setu(ctx, getSetuConfig, config).friend()

                else:
                    logger.warning("无好友的配置文件(0.json)")
                    return


mark_recv(main, author='yuban10703', name="色图", usage='来张色图')
