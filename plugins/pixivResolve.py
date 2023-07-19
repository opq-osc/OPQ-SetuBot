import base64
import re
from io import BytesIO

import httpx
from PIL import Image, ImageFilter
from botoy import S, ctx, mark_recv, logger, jconfig

client_options = dict(proxies=jconfig.get("proxies"), timeout=10)


class PixivResolve:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66"
    }

    def __init__(self, S, pid, page):
        self.pid = pid
        self.page = page
        self.send = S

    async def getSetuInfo(self, pid):
        try:
            async with httpx.AsyncClient(**client_options) as c:
                return (
                    await c.get(
                        "https://www.pixiv.net/touch/ajax/illust/details",
                        params={
                            "illust_id": pid,
                            "ref": "",
                            "lang": "zh",
                        },
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66",
                            "referer": f"https://www.pixiv.net/artworks/{pid}"
                        },
                    )
                ).json()
        except:
            logger.error("Pixiv解析:获取图片信息失败")

    def choosePicUrl(self, info, p):
        if info["page_count"] == "1":
            if p != 0:
                return
            return info["url"]
        else:
            try:
                return info["manga_a"][p]["url"]
            except:
                return

    def buildMsg(self, title, author, authorid, page, pic_url):
        return (
            "标题:{title}\r\n"
            "作者:{author}\r\n"
            "https://www.pixiv.net/users/{authorid}\r\n"
            "P:{page}\r\n"
            "原图:{pic_url}\r\n".format(
                title=title,
                author=author,
                authorid=authorid,
                page=page,
                pic_url=pic_url
            )
        )

    async def url2base64(self, url):
        async with httpx.AsyncClient(
                headers={"Referer": "https://www.pixiv.net"}, **client_options
        ) as client:
            res = await client.get(url)
        with Image.open(BytesIO(res.content)) as pic:
            pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=6.5))  # 高斯模糊
            with BytesIO() as bf:
                pic_Blur.save(bf, format="PNG")
                return base64.b64encode(bf.getvalue()).decode()

    async def check_png_or_jpg(self, url):
        async with httpx.AsyncClient(
                headers={"Referer": "https://www.pixiv.net"}, **client_options
        ) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return url
            else:
                if url[-3:] == "jpg":
                    return url.replace("jpg", "png")
                else:
                    return url.replace("png", "jpg")

    def buildOriginalUrl(self, url: str) -> str:
        # print(url.replace("_master1200", ""))
        info = re.findall(r"/img-master(/img/.*)", url.replace("_master1200", ""))
        # print(info)
        originalUrl = "https://i.pixiv.re/img-original" + info[0]
        return originalUrl

    async def main(self):
        if data := await self.getSetuInfo(self.pid):
            # print(data)
            if picurl := self.choosePicUrl(data["body"]["illust_details"], self.page):
                print(picurl)
                pic_base64 = await self.url2base64(picurl)
                msg = self.buildMsg(
                    data["body"]["illust_details"]["title"],
                    data["body"]["illust_details"]["author_details"]["user_name"],
                    data["body"]["illust_details"]["user_id"],
                    self.page,
                    await self.check_png_or_jpg(self.buildOriginalUrl(picurl)),
                )
                await self.send.image(pic_base64, msg, type=self.send.TYPE_BASE64)
            else:
                await self.send.text("{}无P{}~".format(self.pid, self.page))


async def main():
    if m := (ctx.group_msg or ctx.friend_msg):
        if info := re.match(r".*pixiv.net/artworks/(\d+) ?p?(\d+)?", m.text):
            logger.info("解析Pixiv:{}".format(info[0]))
            try:
                page = 0 if info[2] is None else int(info[2])
                pid = int(info[1])
            except Exception as e:
                logger.error("Pixiv解析:处理数据出错\r\n{}".format(e))
                return
            await PixivResolve(S.bind(ctx), pid, page).main()


mark_recv(main, author='yuban10703', name="解析pixiv链接", usage='发pixiv图片链接')
