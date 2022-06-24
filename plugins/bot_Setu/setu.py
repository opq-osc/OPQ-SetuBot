# -*- coding: utf-8 -*-
# @Time    : 2021/6/20 20:59
# @Author  : yuban10703
import asyncio
import time
from io import BytesIO
from pathlib import Path
from typing import List, Union

import httpx
from botoy import FriendMsg, GroupMsg, S, jconfig, logger
from tenacity import retry, stop_after_attempt, wait_random

from .APIS import Lolicon, Pixiv, Yuban
from .APIS._proxies import async_transport, proxies
from .database import freqLimit, getFriendConfig, getGroupConfig, ifSent
from .model import FinishSetuData, FriendConfig, GetSetuConfig, GroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径

setu_config = jconfig.get_configuration("setu")
base64_send = setu_config.get("base64_send")

logger.warning(f"{'已开启base64发送setu' if base64_send else '未使用base64发送setu'}")


class Setu:
    conversion_for_send_dict = {
        "original": "picOriginalUrl",
        "large": "picLargeUrl",
        "medium": "picMediumUrl",
    }

    def __init__(self, ctx: Union[GroupMsg, FriendMsg], getSetuConfig: GetSetuConfig):
        """
        用正则提取要获取的色图数量,标签,是否R18等信息
        :param ctx: 消息信息
        """
        self.ctx = ctx
        self.send = S.bind(self.ctx)
        self.getSetuConfig = getSetuConfig
        # 要获取色图的信息(数量,tag......)
        if getattr(self.ctx, "type") in ["temp", "group"]:  # 群聊或者群临时会话就加载该群的配置文件
            # getSetuConfig.flagID = self.ctx.QQG
            self.config: GroupConfig = getGroupConfig(  # type:ignore
                getattr(self.ctx, "QQG")
            )
        else:
            # getSetuConfig.flagID = self.ctx.QQ
            self.config: FriendConfig = getFriendConfig()  # type:ignore
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

        if getattr(self.ctx, "type") == "friend":  # 好友会话
            for v in msgDict.values():
                msg += ("" if msg == "" else "\r\n") + v
            return msg
        else:
            for k, v in self.config.setuInfoShow.dict().items():  # type:ignore
                if v:
                    msg += ("" if msg == "" else "\r\n") + msgDict[k]
            if self.config.setting.revokeTime.dict()[self.ctx.type] != 0 and self.ctx.type == "group":  # type: ignore
                msg += "\r\nREVOKE[{}]".format(
                    self.config.setting.revokeTime.dict()[self.ctx.type]  # type:ignore
                )
            if self.config.setting.at:  # type:ignore
                return "\r\n" + msg
            return msg

    async def get(self):
        """
        遍历每个API
        :return:
        """
        conversion_dict = {"Lolicon": "lolicon", "Yuban": "yuban", "Pixiv": "pixiv"}

        for API in [Yuban, Lolicon, Pixiv]:
            if self.config.setting.api.dict()[  # type:ignore
                conversion_dict[API.__name__]
            ]:  # 遍历API的开启状态
                setu_all = await API(self.getSetuConfig).main()
                setu_filtered = await self.filter_Sent(setu_all)
                logger.success(
                    "{}:{} 从API:{}获取到关于{}的色图{}张,去除{}s内重复发送过的后剩余{}张".format(
                        "好友" if self.ctx.type == "friend" else "群",
                        self.ctx.QQ if self.ctx.type == "friend" else self.ctx.QQG,
                        API.__name__,
                        self.getSetuConfig.tags,
                        len(setu_all),
                        self.config.setting.sentRefreshTime,  # type:ignore
                        len(setu_filtered),
                    )
                )
                self.getSetuConfig.doneNum += len(setu_filtered)  # 记录获取到的数量
                if base64_send:
                    await self.sendsetu_forBase64(setu_filtered)
                else:
                    await self.sendsetu_forUrl(setu_filtered)

        if self.getSetuConfig.doneNum == 0:  # 遍历完API一张都没获取到
            await self.send.atext(self.config.replyMsg.notFound)
            return
        if self.getSetuConfig.doneNum < self.getSetuConfig.toGetNum:  # 获取到的数量小于预期
            await self.send.atext(
                self.config.replyMsg.insufficient.format(
                    tag=self.getSetuConfig.tags, num=self.getSetuConfig.doneNum
                )
            )
            return

    async def sendsetu_forUrl(self, setus: List[FinishSetuData]):
        """发送setu,直接传url到OPQ"""

        for setu in setus:
            await self.send.aimage(
                setu.dict()[self.conversion_for_send_dict[self.config.setting.quality]],
                self.buildMsg(setu),
                self.config.setting.at,
                type=self.send.TYPE_URL,
            )

    async def sendsetu_forBase64(self, setus_info: List[FinishSetuData]):
        """发送setu,下载后用Base64发给OPQ"""
        async with httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=8, max_connections=10),
            proxies=proxies,
            transport=async_transport,
            headers={"Referer": "https://www.pixiv.net"},
            timeout=10,
        ) as client:

            @retry(
                stop=stop_after_attempt(3),
                wait=wait_random(min=1, max=2),
                retry_error_callback=lambda retry_state: "https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/error.jpg",
            )
            async def download_setu(url) -> Union[bytes, str]:
                res = await client.get(url)
                if res.status_code != 200:
                    logger.warning("download_setu: res.status_code != 200")
                    raise Exception("download_setu: res.status_code != 200")
                with BytesIO() as bf:
                    bf.write(res.content)
                    bf.write(str(time.time()).encode("utf-8"))  # 增加信息,改变MD5
                    return bf.getvalue()

            for setu in setus_info:
                await self.send.aimage(
                    await download_setu(
                        setu.dict()[
                            self.conversion_for_send_dict[self.config.setting.quality]
                        ]
                    ),
                    self.buildMsg(setu),
                    self.config.setting.at,
                )
                await asyncio.sleep(2)

    async def auth(self) -> bool:
        """
        检查群是否开启setu,r18功能
        :return:
        """
        if not self.config.setting.setu.dict()[self.ctx.type]:  # type: ignore
            await self.send.atext(self.config.replyMsg.closed)
            return False
        if (
            not self.config.setting.r18.dict()[self.ctx.type]  # type: ignore
            and self.getSetuConfig.level > 0
        ):
            await self.send.atext(self.config.replyMsg.noR18)
            return False

        return True

    async def check_parameters(self) -> bool:
        """
        检查数量
        :return:
        """
        if (
            self.getSetuConfig.toGetNum
            > self.config.setting.singleMaximum.dict()[self.ctx.type]  # type:ignore
        ):
            await self.send.atext(self.config.replyMsg.tooMuch)
            return False
        if self.getSetuConfig.toGetNum <= 0:
            await self.send.atext(self.config.replyMsg.tooSmall)
            return False
        if (
            self.config.setting.r18.dict()[self.ctx.type]  # type:ignore
            and self.getSetuConfig.level != 1
        ):  # 群开启了R18,则在非指定r18时返回混合内容
            self.getSetuConfig.level = 2
        return True

    async def filter_Sent(self, setus: List[FinishSetuData]) -> List[FinishSetuData]:
        """过滤一段时间内发送过的图片"""
        if setus != None:
            setus_copy = setus.copy()
            for setu in setus:
                if await ifSent(
                    self.ctx.QQG if self.ctx.type == "group" else self.ctx.QQ,
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
        if self.ctx.type == "group":  # 群聊
            if data := await freqLimit(
                self.ctx.QQG, self.config, self.getSetuConfig
            ):  # 触发频率限制
                freqConfig = data[0]
                data_tmp = data[1]
                await self.send.atext(
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
            await self.send.atext(self.config.replyMsg.closed)
            return
        if not self.config.setting.r18 and self.getSetuConfig.level > 0:
            await self.send.atext(self.config.replyMsg.noR18)
            return
        if self.getSetuConfig.toGetNum > self.config.setting.singleMaximum:
            await self.send.atext(self.config.replyMsg.tooMuch)
            return
        if self.getSetuConfig.toGetNum <= 0:
            await self.send.atext(self.config.replyMsg.tooSmall)
            return
        if (
            self.config.setting.r18 and self.getSetuConfig.level != 1
        ):  # 群开启了R18,则在非指定r18时返回混合内容
            self.getSetuConfig.level = 2
        await self.get()

    async def main(self):
        """群聊和临时会话一起处理
        好友私聊单独处理"""
        if self.ctx.type == "friend":  # 好友会话
            if self.config:  # 如果有好友配置文件(0.json)
                await self.friend()
                return
            else:
                logger.warning("无好友的配置文件(0.json)")
        else:  # 群聊or临时会话
            if self.config:  # 如果有群配置文件
                await self.group_or_temp()
                return
            else:
                logger.warning("无群:{}的配置文件".format(self.ctx.QQG))
        await self.send.atext("无本群配置文件,请联系bot管理员~")
