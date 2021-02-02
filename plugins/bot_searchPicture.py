import requests
from botoy import decorators as deco
from botoy.collection import MsgTypes
from module.send import Send as send
from module import config
import json
from loguru import logger


class SearchPic:
    def __init__(self, ctx):
        self.ctx = ctx

    def buildmsg(self, data: dict):
        msg = '相似度:{}\r\n'.format(data['header']['similarity'])
        for k, v in data['data'].items():
            if type(v) == list:
                v = v[0]
            msg += '{}:{}\r\n'.format(k, v)
        return msg

    def saucenao(self, picurl):
        url = 'https://saucenao.com/search.php'
        params = {'api_key': config.saucenaoApiKey,
                  'db': 999,
                  'output_type': 2,
                  'testmode': 1,
                  'numres': 1,
                  'url': picurl}
        try:
            return requests.get(url, params=params).json()
        except Exception as e:
            logger.warning('saucenao搜图失败~ :{}'.format(e))
            return

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
            send.picture(self.ctx, msg, res['results'][0]['header']['thumbnail'])
            return
        else:
            logger.warning('saucenao无返回')


@deco.ignore_botself
@deco.in_content('.*搜图')
@deco.queued_up
@deco.these_msgtypes(MsgTypes.PicMsg)
def receive_group_msg(ctx):
    SearchPic(ctx).main()


@deco.ignore_botself
@deco.in_content('.*搜图')
@deco.queued_up
@deco.these_msgtypes(MsgTypes.PicMsg)
def receive_friend_msg(ctx):
    SearchPic(ctx).main()
