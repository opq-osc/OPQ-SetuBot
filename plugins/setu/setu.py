# -*- coding: utf-8 -*-
# @Time    : 2021/6/20 20:59
# @Author  : yuban10703
import asyncio
import time
from pathlib import Path
from random import shuffle
from typing import List, Union

import httpx
from botoy import S, jconfig, logger

from .APIS import Lolicon, Pixiv, Yuban
from .database import freqLimit, ifSent, saveMsgSeq
from .model import FinishSetuData, FriendConfig, GetSetuConfig, GroupConfig
from .utils import download_setu

curFileDir = Path(__file__).parent  # 当前文件路径

setu_config = jconfig.get_configuration("setu")


# base64_send = setu_config.get("base64_send")

# logger.warning(f"{'已开启base64发送setu' if base64_send else '未使用base64发送setu'}")


class Setu:
    conversion_for_send_dict = {
        "original": "picOriginalUrl",
        "large": "picLargeUrl",
        "medium": "picMediumUrl",
    }

    def __init__(self, ctx, getSetuConfig: GetSetuConfig, user_config: Union[GroupConfig, FriendConfig]):
        """
        用正则提取要获取的色图数量,标签,是否R18等信息
        :param ctx: 消息信息
        """
        # self.ctx = ctx
        self.send = S.bind(ctx)
        self.getSetuConfig = getSetuConfig
        # 要获取色图的信息(数量,tag......)
        self.config = user_config
        # self.config = None

    def buildMsg(self, setudata: FinishSetuData):
        msgDict = {
            "title": "标题:{}".format(setudata.title),
            "picID": "作品id:{}".format(setudata.picID),
            "picWebUrl": setudata.picWebUrl,
            "page": "page:{}".format(setudata.page),
            "author": "作者:{}".format(setudata.author),
            "authorID": "作者id:{}".format(setudata.authorID),
            "authorWebUrl": setudata.authorWebUrl,
            "picOriginalUrl": "原图:{}".format(setudata.picOriginalUrl_Msg),
            "tags": "Tags:[{}]".format(setudata.tags),
        }
        msg = ""
        # if self.config:  # 群聊和临时

        if self.getSetuConfig.msgtype == "friend":  # 好友会话
            for v in msgDict.values():
                msg += ("" if msg == "" else "\r\n") + v
            return msg
        else:
            for k, v in self.config.setuInfoShow.dict().items():  # type:ignore
                if v:
                    msg += ("" if msg == "" else "\r\n") + msgDict[k]
            # if self.config.setting.revokeTime.dict()[
            #     self.getSetuConfig.msgtype] != 0 and self.getSetuConfig.msgtype == "group":  # type: ignore
            #     msg += "\r\nREVOKE[{}]".format(
            #         self.config.setting.revokeTime.dict()[self.getSetuConfig.msgtype]  # type:ignore
            #     )
            if self.config.setting.at:  # type:ignore
                return "\r\n" + msg
            return msg

    async def get(self):
        """
        遍历每个API
        :return:
        """
        conversion_dict = {"Lolicon": "lolicon", "Yuban": "yuban", "Pixiv": "pixiv"}
        APIS = [Yuban, Lolicon, Pixiv]
        shuffle(APIS)  # 打乱api顺序
        for API in APIS:
            if API.__name__ == "Pixiv" and not setu_config.get("refresh_token"):
                continue
            if self.config.setting.api.dict()[  # type:ignore
                conversion_dict[API.__name__]
            ]:  # 遍历API的开启状态
                setu_all = await API(self.getSetuConfig).main()
                setu_filtered = await self.filter_Sent(setu_all)
                logger.success(
                    "{}:{} 从API:{}获取到关于{}的色图{}张,去除{}s内重复发送过的后剩余{}张".format(
                        "好友" if self.getSetuConfig.msgtype == "friend" else "群",
                        self.getSetuConfig.QQ if self.getSetuConfig.msgtype == "friend" else self.getSetuConfig.QQG,
                        API.__name__,
                        self.getSetuConfig.tags,
                        len(setu_all),
                        self.config.setting.sentRefreshTime,  # type:ignore
                        len(setu_filtered),
                    )
                )
                self.getSetuConfig.doneNum += len(setu_filtered)  # 记录获取到的数量
                await self.sendsetu_forBase64(setu_filtered)

                # if base64_send:
                #     await self.sendsetu_forBase64(setu_filtered)
                # else:
                #     await self.sendsetu_forUrl(setu_filtered)

        if self.getSetuConfig.doneNum == 0:  # 遍历完API一张都没获取到
            await self.send.text(self.config.replyMsg.notFound)
            return
        if self.getSetuConfig.doneNum < self.getSetuConfig.toGetNum:  # 获取到的数量小于预期
            await self.send.text(
                self.config.replyMsg.insufficient.format(
                    tag=self.getSetuConfig.tags, num=self.getSetuConfig.doneNum
                )
            )
            return

    # async def sendsetu_forUrl(self, setus: List[FinishSetuData]):
    #     """发送setu,直接传url到OPQ"""
    #
    #     for setu in setus:
    #         await self.send.image(
    #             setu.dict()[self.conversion_for_send_dict[self.config.setting.quality]],
    #             self.buildMsg(setu),
    #             self.config.setting.at,
    #             type=self.send.TYPE_URL,
    #         )

    async def sendsetu_forBase64(self, setus_info: List[FinishSetuData]):
        """发送setu,下载后用Base64发给OPQ"""
        async with httpx.AsyncClient(
                proxies=jconfig.get("proxies"),
                headers={"Referer": "https://www.pixiv.net"},
                timeout=10,
        ) as client:
            for setu in setus_info:
                data = await self.send.image(
                    await download_setu(
                        client,
                        setu.dict()[
                            self.conversion_for_send_dict[self.config.setting.quality]
                        ],
                    ),
                    self.buildMsg(setu),
                    self.config.setting.at,
                )
                if self.getSetuConfig.msgtype == "group":
                    await saveMsgSeq(group=self.getSetuConfig.QQG, msgseq=data.MsgSeq,
                                     revoke_time=self.config.setting.revokeTime.dict()[self.getSetuConfig.msgtype])
                await asyncio.sleep(2.5)

    async def auth(self) -> bool:
        """
        检查群是否开启setu,r18功能
        :return:
        """
        if not self.config.setting.setu.dict()[self.getSetuConfig.msgtype]:  # type: ignore
            await self.send.text(self.config.replyMsg.closed)
            return False
        if (
                not self.config.setting.r18.dict()[self.getSetuConfig.msgtype]  # type: ignore
                and self.getSetuConfig.level > 0
        ):
            await self.send.text(self.config.replyMsg.noR18)
            return False

        return True

    async def check_parameters(self) -> bool:
        """
        检查数量
        :return:
        """
        if (
                self.getSetuConfig.toGetNum
                > self.config.setting.singleMaximum.dict()[self.getSetuConfig.msgtype]  # type:ignore
        ):
            await self.send.text(self.config.replyMsg.tooMuch)
            return False
        if self.getSetuConfig.toGetNum <= 0:
            await self.send.text(self.config.replyMsg.tooSmall)
            return False
        # if (
        #         self.config.setting.r18.dict()[self.getSetuConfig.msgtype]  # type:ignore
        #         and self.getSetuConfig.level != 1
        # ):  # 群开启了R18,则在非指定r18时返回混合内容
        #     self.getSetuConfig.level = 2
        return True

    async def filter_Sent(self, setus: List[FinishSetuData]) -> List[FinishSetuData]:
        """过滤一段时间内发送过的图片"""
        if setus != None:
            setus_copy = setus.copy()
            for setu in setus:
                if await ifSent(
                        self.getSetuConfig.QQG if self.getSetuConfig.msgtype == "group" else self.getSetuConfig.QQ,
                        int(setu.picID),
                        int(setu.page),
                        self.config.setting.sentRefreshTime,
                ):
                    setus_copy.remove(setu)
            return setus_copy
        return []

    async def group_or_temp(self):
        """
        群和临时消息
        :return:
        """
        if not await self.auth():  # 鉴权
            return
        if not await self.check_parameters():  # 检查数量
            return
        if self.getSetuConfig.msgtype == "group":  # 群聊
            if data := await freqLimit(
                    self.getSetuConfig.QQG, self.config, self.getSetuConfig
            ):  # 触发频率限制
                freqConfig = data[0]
                data_tmp = data[1]
                await self.send.text(
                    self.config.replyMsg.freqLimit.format(
                        time=freqConfig.refreshTime,
                        limitCount=freqConfig.limitCount,
                        callDone=data_tmp["callDone"],
                        r_time=int(
                            freqConfig.refreshTime - (time.time() - data_tmp["time"])
                        ),
                    )
                )
                return
        await self.get()

    async def friend(self):
        """
        好友消息
        :return:
        """
        if not self.config.setting.setu:
            await self.send.text(self.config.replyMsg.closed)
            return
        if not self.config.setting.r18 and self.getSetuConfig.level > 0:
            await self.send.text(self.config.replyMsg.noR18)
            return
        if self.getSetuConfig.toGetNum > self.config.setting.singleMaximum:
            await self.send.text(self.config.replyMsg.tooMuch)
            return
        if self.getSetuConfig.toGetNum <= 0:
            await self.send.text(self.config.replyMsg.tooSmall)
            return
        # if (
        #         self.config.setting.r18 and self.getSetuConfig.level != 1
        # ):  # 群开启了R18,则在非指定r18时返回混合内容
        #     self.getSetuConfig.level = 2
        await self.get()
