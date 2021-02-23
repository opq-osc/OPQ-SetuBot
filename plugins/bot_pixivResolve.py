import requests
import io
import base64
import re
from PIL import Image, ImageFilter
from botoy import GroupMsg, FriendMsg
from botoy import decorators as deco
from module import config, database
from loguru import logger
from module.send import Send as send


class PixivResolve:
    def __init__(self, ctx):
        self.ctx = ctx
        self.qq = ctx.QQ
        self.qqg = ctx.QQG
        self.msgtype = ctx.type
        self.msg = ctx.Content

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
            with requests.session() as s:
                return s.get(url, params=params, headers=headers, timeout=5).json()
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
                                         revoke=20)

    def pictureProcess(self, url):
        with requests.get(url, headers={'Referer': 'https://www.pixiv.net'}) as res:
            pic = Image.open(io.BytesIO(res.content))
            pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=6.5))  # 高斯模糊
            output_buffer = io.BytesIO()
            pic_Blur.save(output_buffer, format='PNG')
            return base64.b64encode(output_buffer.getvalue()).decode()

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
                                    page, picurl[0].replace('i.pximg.net', 'i.pixiv.cat')
                                    )
                send.picture(self.ctx, msg, '', False, False, pic_base64)
            else:
                send.text(self.ctx, '{}无P{}~'.format(pid, page))


re_expression = r'.*pixiv.net/artworks/.*'


@deco.ignore_botself
@deco.with_pattern(re_expression)
def receive_group_msg(ctx: GroupMsg):
    PixivResolve(ctx).main()


@deco.ignore_botself
@deco.with_pattern(re_expression)
def receive_friend_msg(ctx: FriendMsg):
    PixivResolve(ctx).main()
