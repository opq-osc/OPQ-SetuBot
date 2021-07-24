import httpx
from botoy import jconfig, S
from io import BytesIO
import base64
from PIL import Image, ImageFilter
from loguru import logger
import json
from pathlib import Path

curFileDir = Path(__file__).absolute().parent  # 当前文件路径

with open(curFileDir / 'config.json', 'r', encoding='utf-8') as f:
    conf = json.load(f)

from httpx_socks import SyncProxyTransport

if proxies_socks := jconfig.proxies_socks:
    transport = SyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    proxies = jconfig.proxies_http


class SearchPic:
    def __init__(self, ctx):
        self.ctx = ctx
        self.send = S.bind(ctx)

    def buildmsg(self, data: dict):
        msg = '相似度:{}\r\n'.format(data['header']['similarity'])
        for k, v in data['data'].items():
            if type(v) == list:
                v = v[0]
            msg += '{}:{}\r\n'.format(k, v)
        msg += '预览url:{}'.format(data['header']['thumbnail'])
        return msg

    def saucenao(self, picurl):
        url = 'https://saucenao.com/search.php'
        params = {'api_key': conf['saucenaoAPIKEY'],
                  'db': 999,
                  'output_type': 2,
                  'testmode': 1,
                  'numres': 1,
                  'url': picurl}
        try:
            with httpx.Client(proxies=proxies, transport=transport) as client:
                return client.get(url, params=params).json()
        except Exception as e:
            logger.warning('saucenao搜图失败~ :{}'.format(e))
            return

    def pictureProcess(self, url):
        with httpx.Client(proxies=proxies, transport=transport) as client:
            res = client.get(url)
        pic = Image.open(BytesIO(res.content))
        pic_Blur = pic.filter(ImageFilter.GaussianBlur(radius=1.8))  # 高斯模糊
        with BytesIO() as bf:
            pic_Blur.save(bf, format='JPEG')
            return base64.b64encode(bf.getvalue()).decode()

    def main(self):
        content = json.loads(self.ctx.Content)
        if content['Tips'] == '[群图片]':
            picurl = content['GroupPic'][0]['Url']
        # elif content['Tips'] == '[好友图片]':
        #     picurl = content['FriendPic'][0]['Url']
        else:
            return
        if res := self.saucenao(picurl):
            msg = self.buildmsg(res['results'][0])
            self.send.image(self.pictureProcess(res['results'][0]['header']['thumbnail']), msg)
            return
        else:
            logger.warning('saucenao无返回')
