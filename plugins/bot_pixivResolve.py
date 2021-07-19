import httpx
from io import BytesIO
import base64
import re
from PIL import Image, ImageFilter
from botoy import GroupMsg, FriendMsg, S, jconfig
from botoy import decorators as deco
from loguru import logger

__doc__ = """解析Pixiv链接,发送Pixiv的链接就行,如果要查看第一页 就在链接加上空格再接p1"""

class PixivResolve:
    def __init__(self, ctx):
        self.ctx = ctx
        self.qq = ctx.QQ
        self.qqg = ctx.QQG
        self.msgtype = ctx.type
        self.msg = ctx.Content
        self.send = S.bind(ctx)

    def getSetuInfo(self, pid):
        url = 'https://www.pixiv.net/touch/ajax/illust/details'
        params = {
            'illust_id': pid,
            'ref': 'https://www.pixiv.net/',
            'lang': 'zh'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66'
        }
        try:
            with httpx.Client(proxies=jconfig.proxies) as c:
                return c.get(url, params=params, headers=headers, timeout=5).json()
        except:
            logger.error('Pixiv解析:获取图片信息失败')
            return

    def choosePicUrl(self, info, p):
        if info['page_count'] == '1':
            if p != 0:
                return
            return info['url_big'], info['url']
        else:
            try:
                return info['manga_a'][p]['url_big'], info['manga_a'][p]['url']
            except:
                return

    def buildMsg(self, title, author, authorid, page, pic_url):

        return '标题:{title}\r\n' \
               '作者:{author}\r\n' \
               'https://www.pixiv.net/users/{authorid}\r\n' \
               'P:{page}\r\n' \
               '原图:{pic_url}\r\n' \
               'REVOKE[{revoke}]'.format(title=title,
                                         author=author,
                                         authorid=authorid,
                                         page=page,
                                         pic_url=pic_url,
                                         revoke=35)

    def pictureProcess(self, url):
        with httpx.stream("GET", url, headers={'Referer': 'https://www.pixiv.net'}, proxies=jconfig.proxies) as res:
            pic = Image.open(BytesIO(res.read()))
            pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=6.5))  # 高斯模糊
            with BytesIO() as bf:
                pic_Blur.save(bf, format='PNG')
                return base64.b64encode(bf.getvalue()).decode()

    def buildOriginalUrl(self, original_url: str, page: int) -> str:
        def changePage(matched):
            if page > 1:
                return '-%s' % (int(matched[0][-1]) + 1)
            else:
                return ''

        msg_changeHost = re.sub(r'//.*/', r'//pixiv.re/', original_url)
        return re.sub(r'_p\d+', changePage, msg_changeHost)

    def main(self):
        logger.info('解析Pixiv:{}'.format(self.msg))
        raw_info = re.match(r'.*pixiv.net/artworks/(.*)', self.msg)
        info_list = raw_info[1].split()
        if len(info_list) > 2:
            pass
            return
        elif len(info_list) == 1:
            try:
                pid = int(info_list[0])
                page = 0
            except:
                return
        elif len(info_list) == 2:
            try:
                pid = int(info_list[0])
                page = int(re.match('p(\d+)', info_list[1])[1])
            except:
                return
        else:
            return
        if data := self.getSetuInfo(pid):
            # print(self.buildMsg(data, page))
            if picurl := self.choosePicUrl(data['body']['illust_details'], page):
                pic_base64 = self.pictureProcess(picurl[1])
                msg = self.buildMsg(data['body']['illust_details']['title'],
                                    data['body']['illust_details']['author_details']['user_name'],
                                    data['body']['illust_details']['user_id'],
                                    page,
                                    self.buildOriginalUrl(picurl[0], int(data['body']['illust_details']['page_count']))
                                    )
                self.send.image(pic_base64, msg)
            else:
                self.send.text('{}无P{}~'.format(pid, page))


re_expression = r'.*pixiv.net/artworks/.*'

@deco.with_pattern(re_expression)
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    PixivResolve(ctx).main()

@deco.with_pattern(re_expression)
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):
    PixivResolve(ctx).main()
