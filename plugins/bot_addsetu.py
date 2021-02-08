import requests
import os
import re
from botoy import GroupMsg, FriendMsg
from botoy import decorators as deco
from module import config, database
from loguru import logger
from module.send import Send as send

# proxies = {"http": "socks5h://127.0.0.1:10808", "https": "socks5h://127.0.0.1:10808"}
proxies = None


class AddSetu:
    def __init__(self, ctx):
        self.ctx = ctx
        self.qq = ctx.QQ
        self.qqg = ctx.QQG
        self.msgtype = ctx.type
        self.msg = ctx.Content
        self.data = None
        self.dataList = []

    def _buildData(self, title, artworkID, author, artistID, page, tags, url, url_big):
        return {'title': title,
                'artwork': int(artworkID),
                'author': re.sub(r'[@,＠].*$', '', author),
                'artist': int(artistID),
                'page': int(page),
                'tags': tags,
                'type': {'normal': [], 'sexy': [], 'porn': []},  # 占位
                'original': url_big,
                'large': url}

    def _processing(self, data):
        datalist = []
        tags = []
        for tag in data['illust_details']['display_tags']:  # 轮询tags
            tags.append({'name': tag['tag']})
            if tag.get('translation') != None:  # None就没有必要存了
                tags.append({'name': tag['translation']})
        if data['illust_details']['page_count'] == '1':
            datalist.append(self._buildData(data['illust_details']['title'],
                                            data['illust_details']['id'],
                                            data['author_details']['user_name'],
                                            data['illust_details']['user_id'],
                                            0,
                                            tags,
                                            data['illust_details']['url'],
                                            data['illust_details']['url_big']))
        else:
            for urldata in data['illust_details']['manga_a']:
                datalist.append(self._buildData(data['illust_details']['title'],
                                                data['illust_details']['id'],
                                                data['author_details']['user_name'],
                                                data['illust_details']['user_id'],
                                                urldata['page'],
                                                tags,
                                                urldata['url'],
                                                urldata['url_big']))
        return datalist

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
            data = requests.get(url, params=params, headers=headers, proxies=proxies).json()
        except:
            logger.error('获取图片信息失败')
            return
        return self._processing(data['body'])

    def addsetu(self, pid, groupid, level, page=None):
        data = self.getSetuInfo(pid)
        if page != None:
            try:
                database.LocalSetu.addSetu(data[page], level, groupid)
            except:
                send.text(self.ctx, 'page错误????')
                return
            send.text(self.ctx, 'addsetu:\npid:{} p{} \n{}'.format(data[page]['artwork'], data[page]['page'],
                                                                   data[page]['original'].replace('i.pximg.net',
                                                                                                  'i.pixiv.cat')))
        else:
            msg = 'addsetu:\npid:{}\n'.format(data[0]['artwork'])
            for d in data:
                database.LocalSetu.addSetu(d, level, groupid)
                msg += 'p{}\n{}\n'.format(d['page'], d['original'].replace('i.pximg.net', 'i.pixiv.cat'))
            send.text(self.ctx, msg)

    def delsetu(self, pid: int, groupid: int, page: int = None):
        if database.LocalSetu.delSetu(pid, groupid, page):
            if page == None:
                send.text(self.ctx, '已删除pid{}的所有p'.format(pid))
            else:
                send.text(self.ctx, '已删除pid{}的p{}'.format(pid, page))
        else:
            send.text(self.ctx, '不存在pid:{}的setu'.format(pid))

    def main(self):  # 权限:非superadmin只能添加本群的图片
        if cmdLv := self.ctx.accessLevel:
            if cmdLv <= 3:
                if info := re.match('addsetu (\d+) l(\d+)$', self.msg):
                    self.addsetu(int(info[1]), self.qqg, int(info[2]))
                elif info := re.match('addsetu (\d+) p(\d+) l(\d+)$', self.msg):
                    self.addsetu(int(info[1]), self.qqg, int(info[3]), int(info[2]))
                elif info := re.match('delsetu (\d+)$', self.msg):
                    self.delsetu(int(info[1]), self.qqg)
                elif info := re.match('delsetu (\d+) p(\d+)$', self.msg):
                    self.delsetu(int(info[1]), self.qqg, int(info[2]))
            if cmdLv == 1:
                if info := re.match('addsetu (\d+) p(\d+) l(\d+) g(\d+)$', self.msg):  # 指定P添加
                    pid = info[1]
                    page = int(info[2])
                    level = int(info[3])
                    groupid = int(info[4])
                    self.addsetu(pid, groupid, level, page)
                elif info := re.match('addsetu (\d+) l(\d+) g(\d+)$', self.msg):
                    pid = info[1]
                    level = int(info[2])
                    groupid = int(info[3])
                    self.addsetu(pid, groupid, level)
                elif info := re.match('delsetu (\d+) g(\d+)$', self.msg):
                    self.delsetu(int(info[1]), int(info[2]))
                elif info := re.match('delsetu (\d+) p(\d+) g(\d+)$', self.msg):
                    self.delsetu(int(info[1]), int(info[3]), int(info[2]))


@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    AddSetu(ctx).main()


@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):
    AddSetu(ctx).main()
