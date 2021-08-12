import base64
import re
from io import BytesIO
from typing import Union

import httpx
from PIL import Image, ImageFilter
from botoy import FriendMsg, GroupMsg, S, logger, jconfig
from botoy import decorators as deco
from httpx_socks import SyncProxyTransport

if proxies_socks := jconfig.proxies_socks:
    transport = SyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    proxies = jconfig.proxies_http

client_options = dict(proxies=proxies, transport=transport, timeout=10)

__doc__ = """解析Pixiv链接,发送Pixiv的链接就行,如果要查看第一页 就在链接加上空格再接p1"""


class PixivResolve:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66"
    }

    def __init__(self, ctx: Union[GroupMsg, FriendMsg]):
        self.ctx = ctx
        self.qq = ctx.QQ  # type:ignore
        self.qqg = ctx.QQG  # type:ignore
        self.msgtype = ctx.MsgType
        self.msg = ctx.Content
        self.send = S.bind(ctx)

    def getSetuInfo(self, pid):
        try:
            with httpx.Client(**client_options) as c:
                return c.get(
                    "https://www.pixiv.net/touch/ajax/illust/details",
                    params={
                        "illust_id": pid,
                        "ref": "https://www.pixiv.net/",
                        "lang": "zh",
                    },
                    headers=self.headers,
                ).json()
        except:
            logger.error("Pixiv解析:获取图片信息失败")

    def choosePicUrl(self, info, p):
        if info["page_count"] == "1":
            if p != 0:
                return
            return info["url_big"], info["url"]
        else:
            try:
                return info["manga_a"][p]["url_big"], info["manga_a"][p]["url"]
            except:
                return

    def buildMsg(self, title, author, authorid, page, pic_url):
        return (
            "标题:{title}\r\n"
            "作者:{author}\r\n"
            "https://www.pixiv.net/users/{authorid}\r\n"
            "P:{page}\r\n"
            "原图:{pic_url}\r\n"
            "REVOKE[{revoke}]".format(
                title=title,
                author=author,
                authorid=authorid,
                page=page,
                pic_url=pic_url,
                revoke=35,
            )
        )

    def url2base64(self, url):
        with httpx.Client(
                headers={"Referer": "https://www.pixiv.net"}, **client_options
        ) as client:
            res = client.get(url)
        with Image.open(BytesIO(res.content)) as pic:
            pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=6.5))  # 高斯模糊
            with BytesIO() as bf:
                pic_Blur.save(bf, format="PNG")
                return base64.b64encode(bf.getvalue()).decode()

    def buildOriginalUrl(self, original_url: str, page: int) -> str:
        return re.sub(
            r"_p\d+",
            lambda m: "-%d" % (int(m[0][2:]) + 1) if page > 1 else "",
            re.sub(r"//.*/", r"//pixiv.re/", original_url),
        )

    def main(self):
        raw_info = getattr(self.ctx, "_match")
        logger.info("解析Pixiv:{}".format(raw_info[0]))
        try:
            page = 0 if raw_info[2] is None else int(raw_info[2])
            pid = int(raw_info[1])
        except Exception as e:
            logger.error('Pixiv解析:处理数据出错\r\n{}'.format(e))
            return
        if data := self.getSetuInfo(pid):
            if picurl := self.choosePicUrl(data["body"]["illust_details"], page):
                pic_base64 = self.url2base64(picurl[1])
                msg = self.buildMsg(
                    data["body"]["illust_details"]["title"],
                    data["body"]["illust_details"]["author_details"]["user_name"],
                    data["body"]["illust_details"]["user_id"],
                    page,
                    self.buildOriginalUrl(
                        picurl[0], int(data["body"]["illust_details"]["page_count"])
                    ),
                )
                self.send.image(pic_base64, msg)
            else:
                self.send.text("{}无P{}~".format(pid, page))


@deco.ignore_botself
@deco.on_regexp(r".*pixiv.net/artworks/(\d+) ?p?(\d+)?")
def main(ctx):
    PixivResolve(ctx).main()


def receive_group_msg(ctx):
    main(ctx)


def receive_friend_msg(ctx):
    main(ctx)
