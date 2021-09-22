import base64
import json
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageFilter
from botoy import FriendMsg, GroupMsg, S, jconfig, logger
from botoy.parser import friend as fp
from botoy.parser import group as gp
from httpx_socks import AsyncProxyTransport

curFileDir = Path(__file__).absolute().parent  # 当前文件路径

try:
    with open(curFileDir / "config.json", "r", encoding="utf-8") as f:
        conf = json.load(f)
    if not conf["APIKEY"]:
        logger.error("[searchPicture]: 请配置API KEY: saucenaoAPIKEY")
        exit(0)
except:
    logger.error("载入saucenaoAPIKEY配置文件(plugins/bot_Search_Picture/config.json)出错")
    exit(0)

if proxies_socks := jconfig.proxies_socks:
    transport = AsyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    proxies = jconfig.proxies_http

client_options = dict(proxies=proxies, transport=transport, timeout=20)


class SearchPic:
    def __init__(self, ctx):
        self.ctx = ctx
        self.send = S.bind(ctx)

    def buildmsg(self, data: dict):
        msg = "相似度:{}\r\n".format(data["header"]["similarity"])
        for k, v in data["data"].items():
            if type(v) == list:
                v = v[0]
            msg += "{}:{}\r\n".format(k, v)
        msg += "预览url:{}".format(data["header"]["thumbnail"])
        return msg

    async def saucenao(self, picurl):
        url = "https://saucenao.com/search.php"
        params = {
            "api_key": conf["APIKEY"],
            "db": 999,
            "output_type": 2,
            "testmode": 1,
            "numres": 1,
            "url": picurl,
        }
        try:

            async with httpx.AsyncClient(**client_options) as client:
                return (await client.get(url, params=params)).json()
        except Exception as e:
            logger.warning("saucenao搜图失败~ :{}".format(e))
        return None

    async def pictureProcess(self, url):
        try:
            async with httpx.AsyncClient(**client_options) as client:
                content = (await client.get(url)).content
            with Image.open(BytesIO(content)) as pic:
                pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=1.8))  # 高斯模糊
                with BytesIO() as bf:
                    pic_Blur.save(bf, format="JPEG")
                    return base64.b64encode(bf.getvalue()).decode()
        except Exception as e:
            logger.warning("saucenao处理图片失败: %s" % e)

    async def main(self):
        picurl = None

        if isinstance(self.ctx, GroupMsg):
            group_pic = gp.pic(self.ctx)
            if group_pic:
                picurl = group_pic.GroupPic[0].Url
        elif isinstance(self.ctx, FriendMsg):
            friend_pic = fp.pic(self.ctx)
            if friend_pic:
                picurl = friend_pic.FriendPic[0].Url

        if picurl:

            if res := await self.saucenao(picurl):
                msg = self.buildmsg(res["results"][0])
                pic = await self.pictureProcess(
                    res["results"][0]["header"]["thumbnail"]
                )
                if pic:
                    await self.send.aimage(pic, msg, type=self.send.TYPE_BASE64)
                else:
                    await self.send.atext(msg)
            else:
                logger.warning("saucenao无返回")
                await self.send.atext("没搜到")
