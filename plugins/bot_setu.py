from botoy import GroupMsg, FriendMsg
from botoy import decorators as deco
from module.send import Send as send
from module.pixivApi import pixiv
from module import config, database
from loguru import logger
import re
import random
import requests
import time
setuPattern = '来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩😍🐍][图圖🤮]'
# session = requests.session()

class Setu:
    def __init__(self, ctx):
        self.ctx = ctx
        info = re.search(setuPattern, ctx.Content)  # 提取关键字
        self.SetuCount: str = info[1]
        self.tags = [i for i in list(set(re.split(r'[,， ]', info[2]))) if i != '']  # 分割tag+去重+去除空元素
        self.r18Keyword: str = info[3]  # r18关键字
        # -----------------------------------
        self.getCountList = [0, 0, 0, 0]  # 各api获取到的数量
        self.config = {'count': 0}  # 待载入的配置:群config

    def replaceLink(self, url: str):  # 把原pixiv链接换成i.pixiv.cat链接
        return url.replace('i.pximg.net', 'i.pixiv.cat')  # 替换字符串

    # def randomMsg(self, msg: list):
    #     return random.choice(msg)
    #
    # def buildOriginalUrl(self, largeUrl):
    #     return re.findall('img/(.*)', largeUrl)[0].replace('_master1200', '')

    def build_msg(self, title_in, artworkid_in, author_in, artistid_in, page_in, url_original_in):
        msg = ''
        msgDict = {
            'pid': '作品id:{}'.format(artworkid_in),
            'purl': 'www.pixiv.net/artworks/' + str(artworkid_in),
            'title': '标题:{}'.format(title_in),
            'uid': '作者id:{}'.format(artistid_in),
            'uurl': 'www.pixiv.net/users/' + str(artistid_in),
            'author': '作者:{}'.format(author_in),
            'page': 'page:{}'.format(page_in),
            'url_original': '原图:{}'.format(url_original_in)
        }
        for k, v in self.config['setuinfo'].items():
            if v:
                msg += '\r\n' + msgDict[k]
        if self.config['returnTags'] and len(self.tags) >= 1:  # 显示tag
            msg += '\r\nTAG:{}'.format(self.tags)
        if self.config['type'] == 'group':
            if self.config['revoke']:  # 群聊并且开启撤回
                msg += '\r\nREVOKE[{}]'.format(self.config['revoke'])
            if self.config['at']:
                return '\r\n' + msg
        return msg

    def localSetu(self):
        if self.config['count'] == sum(self.getCountList):  # 如果上面的api已经获取了足够的数量
            return
        res = database.LocalSetu.getSetu(self.ctx.QQG, self.config['setuLevel'], self.config['count'],
                                         self.tags)
        for data in res:
            if database.Setu.ifSent(self.config['callid'], data['original'],
                                    self.config['refreshSent']):  # 判断是否发送过
                continue
            msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'],
                                 data['page'], self.replaceLink(data['original']))  # 组装消息
            if self.config['original']:  # 是否发送原图
                send.picture(self.ctx, msg, self.replaceLink(data['original']) if config.proxy else data['original'],
                             False, self.config['at'])
            else:
                send.picture(self.ctx, msg, self.replaceLink(data['large']) if config.proxy else data['large'], False,
                             self.config['at'])
            self.getCountList[0] += 1
        logger.info(
            '从本地数据库获取到{}张关于{}的setu  实际发送{}张'.format(len(res), self.tags,
                                                    self.getCountList[0]))  # 打印获取到多少条

    def api_0(self):
        if not config.api_yuban10703:
            return
        if self.config['count'] == sum(self.getCountList):  # 如果上面的api已经获取了足够的数量
            return
        url = 'http://api.yuban10703.xyz:2333/setu_v4'
        params = {'level': self.config['setuLevel'],
                  'num': self.config['count'] - sum(self.getCountList),
                  'tag': self.tags}
        if self.config['count'] > 10:  # api限制不能大于10
            params['num'] = 10
        try:
            with requests.session() as s:
                res = s.get(url, params=params, timeout=5)
            setu_data = res.json()
        except Exception as e:
            logger.warning('api0 boom~ :{}'.format(e))
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    if database.Setu.ifSent(self.config['callid'], data['original'],
                                            self.config['refreshSent']):  # 判断是否发送过
                        continue
                    url_original = self.replaceLink(data['original']) if config.proxy else data['original']  # 原图链接
                    url_large = self.replaceLink(data['large']) if config.proxy else data['large']  # 高清链接
                    msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'],
                                         data['page'], self.replaceLink(data['original']))  # 组装消息
                    if self.config['original']:  # 是否发送原图
                        send.picture(self.ctx, msg, url_original, False, self.config['at'])
                    else:
                        send.picture(self.ctx, msg, url_large.replace('600x1200_90_webp', '600x1200_90'), False,
                                     self.config['at'])
                    self.getCountList[1] += 1
            logger.info(
                '从yubanのapi获取到{}张关于{}的setu  实际发送{}张'.format(setu_data['count'], self.tags,
                                                            self.getCountList[1]))  # 打印获取到多少条

    def api_1(self):
        if not config.api_lolicon:
            return
        if self.config['count'] == sum(self.getCountList):  # 如果上面的api已经获取了足够的数量
            return
        # 兼容api0
        if self.config['setuLevel'] == 1:
            r18 = 0
        elif self.config['setuLevel'] == 3:
            r18 = 2
        elif self.config['setuLevel'] == 2:
            r18 = 1
        else:
            r18 = 0
        url = 'https://api.lolicon.app/setu'
        params = {'r18': r18,
                  'apikey': config.loliconApiKey,
                  'num': self.config['count'] - sum(self.getCountList),
                  'size1200': not bool(self.config['original'])}
        if self.config['count'] > 10:
            params['num'] = 10
        if len(self.tags) != 1 or (len(self.tags[0]) != 0 and not self.tags[0].isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            params['keyword'] = self.tags
        if not config.proxy:  # 不开启反代
            params['proxy'] = 'disable'
        try:
            with requests.session() as s:
                res = s.get(url, params=params, timeout=8)
            setu_data = res.json()
        except Exception as e:
            logger.warning('api1 boom~ :{}'.format(e))
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    if database.Setu.ifSent(self.config['callid'], data['url'],
                                            self.config['refreshSent']):  # 判断是否发送过

                        continue
                    msg = self.build_msg(
                        data['title'], data['pid'], data['author'], data['uid'], data['p'],
                        'https://i.pixiv.cat/img-original/img/{}'.format(
                            re.findall('img/(.*)', data['url'])[0].replace('_master1200', '')
                        )
                    )
                    send.picture(self.ctx, msg, data['url'], False, self.config['at'])
                    self.getCountList[2] += 1
                logger.info(
                    '从loliconのapi获取到{}张关于{}的setu  实际发送{}张'.format(setu_data['count'], self.tags,
                                                                  self.getCountList[2]))  # 打印获取到多少条
            else:
                logger.warning('api1:{}'.format(res.status_code))

    def api_pixiv(self):  # p站热度榜
        if not config.api_pixiv:
            return
        if self.config['count'] == sum(self.getCountList):  # 如果上面的api已经获取了足够的数量
            return
        # 兼容api0
        if self.config['setuLevel'] == 1:
            r18 = 0
        elif self.config['setuLevel'] == 3:
            r18 = random.choice([0, 1])
        elif self.config['setuLevel'] == 2:
            r18 = 1
        else:
            r18 = 0
        data = pixiv.pixivSearch(self.tags, bool(r18))
        for setu in data['illusts']:
            if sum(self.getCountList) == self.config['count']:
                break
            if setu['page_count'] != 1:  # 多页画廊
                continue
            if setu['x_restrict'] == 2:  # R18G
                continue
            if self.config['setuLevel'] in [0, 1] and setu['x_restrict'] == 1:  # R18
                continue
            if database.Setu.ifSent(self.config['callid'], setu['meta_single_page']['original_image_url'],
                                    self.config['refreshSent']):
                continue
            url_original = self.replaceLink(setu['meta_single_page']['original_image_url']) if config.proxy else \
                setu['meta_single_page']['original_image_url']  # 原图链接
            url_large = self.replaceLink(setu['image_urls']['large']) if config.proxy else setu['image_urls'][
                'large']  # 高清链接
            msg = self.build_msg(setu['title'], setu['id'], setu['user']['name'], setu['user']['id'], 1,
                                 self.replaceLink(setu['meta_single_page']['original_image_url']))
            if self.config['original']:  # 原图
                send.picture(self.ctx, msg, url_original, False,
                             self.config['at'])
            else:
                url_large.replace('600x1200_90_webp', '600x1200_90')  # 更换为非webp的链接
                send.picture(self.ctx, msg, url_large, False, self.config['at'])
            self.getCountList[3] += 1
        logger.info(
            '从Pixiv热度榜获取到{}张setu  实际发送{}张'.format(len(data['illusts']), self.getCountList[3]))  # 打印获取到多少条

    # def api2(self):
    #     if self.config['count'] == sum(self.getCountList):  # 如果上面的api已经获取了足够的数量
    #         return
    #     togetcount = self.config['count'] - sum(self.getCountList)
    #     pass
    def freq(self):
        if freqinfo := database.Setu.freq(self.ctx.QQG, self.config['count'], self.config['refreshTime'],
                                          self.config['freq']):
            msg = self.config['msg_frequency'].format(
                time=self.config['refreshTime'],
                num=self.config['freq'],
                num_call=freqinfo[0],
                r_time=round(self.config['refreshTime'] - (time.time() - freqinfo[1]))
            )
            send.text(self.ctx, msg, self.config['at_warning'])
            return True
        return False

    def processing_and_inspect(self):  # 处理消息+调用
        # -----------------------------------------------
        if self.SetuCount != '':  # 如果指定了数量
            try:
                self.config['count'] = int(self.SetuCount)
            except:  # 出错就说明不是数字
                send.text(self.ctx, self.config['msg_inputError'], self.config['at_warning'])
                return
            if self.config['count'] <= 0:  # ?????
                send.text(self.ctx, self.config['msg_lessThan0'], self.config['at_warning'])
                return
        else:  # 未指定默认1
            self.config['count'] = 1
        # -----------------------------------------------
        if self.config['type'] in ['group', 'temp']:  # 群聊和临时会话
            if not self.config['setu']:  # 如果没开启色图
                send.text(self.ctx, self.config['msg_setuClosed'], self.config['at_warning'])
                return
            if self.config['count'] > self.config['maxnum']:  # 大于单次最大数量
                send.text(self.ctx, self.config['msg_tooMuch'], self.config['at_warning'])
                return
            if self.r18Keyword != '':  # 正则匹配到开启r18的关键字
                if self.config['r18']:  # 开启了r18
                    self.config['setuLevel'] = 2
                else:
                    send.text(self.ctx, self.config['msg_r18Closed'], self.config['at_warning'])
                    return
            if self.freq():  # 频率控制,仅群聊和临时会话
                return
        elif self.config['type'] == 'friend':
            if self.r18Keyword != '':  # 好友会话无限制
                self.config['setuLevel'] = 2
        self.send()

    def group_or_temp(self):  # 读数据库+鉴权+判断开关
        if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
            self.config['type'] = 'group'
            self.config['callqq'] = self.ctx.FromUserId
            self.config['callid'] = self.ctx.FromGroupId
        elif self.ctx.MsgType == 'TempSessionMsg':  # 临时会话
            self.config['callqq'] = self.ctx.FromUin
            self.config['callid'] = self.ctx.TempUin
            self.config['type'] = 'temp'
        if data := database.Setu.getGroupConf(self.ctx.QQG, self.ctx.type):  # 查询group数据库数据
            self.config.update(data)
            self.processing_and_inspect()
        else:
            send.text(self.ctx, '数据库无群:{}信息,请联系管理员~'.format(self.config['callid']))
            logger.error('数据库无群:{} 信息'.format(self.config['callid']))
            return

    def friend(self):
        self.config['type'] = 'friend'
        self.config['callqq'] = self.ctx.FromUin
        self.config['callid'] = self.ctx.FromUin
        self.config.update(database.Setu.getUserconf(self.ctx.QQ))  # 载入自定义数据
        self.processing_and_inspect()

    def main(self):  # 判断消息类型给对应函数处理
        if self.ctx.type == 'friend':  # 好友会话
            self.friend()
        else:  # 群聊or临时会话
            self.group_or_temp()

    def send(self):
        # logger.info('开始')
        apis = [self.localSetu, self.api_0]
        func = random.choice(apis)
        apis.remove(func)
        func()
        apis[0]()
        if len(self.tags) in [0, 1]:  # api1不支持多tag
            self.api_1()
        if len(self.tags) != 0:
            self.api_pixiv()
        if sum(self.getCountList) == 0:
            send.text(self.ctx, self.config['msg_notFind'], self.config['at_warning'])
            return
        elif sum(self.getCountList) < self.config['count']:
            send.text(self.ctx, self.config['msg_insufficient'].format(
                tag=self.tags,
                num=sum(self.getCountList)
            ), self.config['at_warning'])
        # logger.info('结束')


@deco.ignore_botself
@deco.with_pattern(setuPattern)
def receive_group_msg(ctx: GroupMsg):
    Setu(ctx).main()


@deco.ignore_botself
@deco.with_pattern(setuPattern)
def receive_friend_msg(ctx: FriendMsg):
    Setu(ctx).main()
