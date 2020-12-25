from iotbot import IOTBOT, Action, FriendMsg, GroupMsg, EventMsg
import iotbot.decorators as deco
from iotbot.refine import *
# from iotbot.sugar import Text, Picture
from PIL import Image
from retrying import retry
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.operations import add
from loguru import logger
import base64
import threading
import requests
import random
import time
import re
import json
import sys
import os
import io
from datetime import datetime
import hashlib
import uuid
import pathlib

try:
    with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
        config = json.loads(f.read())
        logger.success('加载config.json成功~')
except:
    logger.error('config.json加载失败,请检查配置~')
    sys.exit()
try:
    pathlib.Path('db').mkdir()
    logger.success('db创建成功')
except:
    logger.info('db目录已存在')
bot = IOTBOT(config['botQQ'], log=False)
action = Action(bot, queue=False)
pattern_setu = '来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩😍🐍][图圖🤮]'
# ------------------db-------------------------
group_config = TinyDB('./db/group_config.json')
friend_config = TinyDB('./db/friend_config.json')
tagdb = TinyDB('./db/tag.json')
db_tmp = TinyDB(storage=MemoryStorage)
Q = Query()


# ---------------------------------------------


class Send:
    def send_text(self, ctx, text, atUser: bool = False):
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.send_group_text_msg(ctx.FromGroupId, text, ctx.FromUserId)
            else:
                action.send_group_text_msg(ctx.FromGroupId, text)
        else:
            if ctx.TempUin == None:  # None为好友会话
                action.send_friend_text_msg(ctx.FromUin, text)
            else:  # 临时会话
                action.send_private_text_msg(ctx.FromUin, text, ctx.TempUin)
        return

    def send_pic(self, ctx, text='', picUrl='', flashPic=False, atUser: bool = False, picBase64Buf='', fileMd5=[]):
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.send_group_pic_msg(ctx.FromGroupId, picUrl, flashPic, ctx.FromUserId, text, picBase64Buf,
                                          fileMd5, timeout=15)
            else:
                action.send_group_pic_msg(ctx.FromGroupId, picUrl, flashPic, 0, text, picBase64Buf, fileMd5, timeout=15)
        else:
            if ctx.TempUin == None:
                action.send_friend_pic_msg(ctx.FromUin, text, picUrl, picBase64Buf, fileMd5, flashPic, timeout=15)
            else:
                action.send_private_pic_msg(ctx.FromUin, ctx.TempUin, picUrl, picBase64Buf, text, fileMd5, timeout=15)
        return

    # ---------------------------------------------


sendMsg = Send()


# ---------------------------------------------
class PixivToken:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.device_token = uuid.uuid4().hex
        self.api = 'https://oauth.secure.pixiv.net/auth/token'

    def headers(self):
        hash_secret = '28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c'
        X_Client_Time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+08:00')
        X_Client_Hash = hashlib.md5((X_Client_Time + hash_secret).encode('utf-8')).hexdigest()
        headers = {'User-Agent': 'PixivAndroidApp/5.0.197 (Android 10; Redmi 4)',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept-Language': 'zh_CN_#Hans',
                   'App-OS': 'android',
                   'App-OS-Version': '10',
                   'App-Version': '5.0.197',
                   'X-Client-Time': X_Client_Time,
                   'X-Client-Hash': X_Client_Hash,
                   'Host': 'oauth.secure.pixiv.net',
                   'Accept-Encoding': 'gzip'}
        return headers

    def get_token(self):
        logger.info('获取Pixiv_token~')
        data = {'client_id': 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
                'client_secret': 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
                'grant_type': 'password',
                'username': self.username,
                'password': self.password,
                'device_token': self.device_token,
                'get_secure_url': 'true',
                'include_policy': 'true'}
        try:
            res = requests.post(url=self.api, data=data, headers=self.headers()).json()
        except:
            logger.error('获取token出错~')
            bot.close()
            return
        res['time'] = time.time()  # 记录时间
        return res

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def refresh_token(self, token):
        logger.info('刷新Pixiv_token~')
        data = {'client_id': 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
                'client_secret': 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
                'grant_type': 'refresh_token',
                'refresh_token': token,
                'device_token': self.device_token,
                'get_secure_url': 'true',
                'include_policy': 'true'}
        res = requests.post(url=self.api, data=data, headers=self.headers()).json()
        res['time'] = time.time()
        return res

    def if_refresh_token(self):
        global pixivid
        while True:
            if time.time() - pixivid['time'] >= int(pixivid['expires_in']):  # 刷新
                try:
                    pixivid = self.refresh_token(pixivid['refresh_token'])
                    logger.success('刷新token成功~')
                    self.saveToken(pixivid)
                except:
                    logger.warning('刷新Pixiv_token出错')
                    time.sleep(10)
            else:
                time.sleep(int(pixivid['expires_in']) - (time.time() - pixivid['time']))

    def saveToken(self, data):
        with open('.Pixiv_Token.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(data))
        logger.success('PixivToken已保存到.Pixiv_Token.json')
        return


class Setu:
    def __init__(self, ctx, tag, num, whether_r18):
        self.ctx = ctx
        self.num = num
        self.tag = [i for i in list(set(re.split(r',|，|\.|-| |_|/|\\', tag))) if i != '']  # 分割tag+去重+去除空元素
        # -----------------------------------
        self.setu_level = 1
        self.r18_OnOff_keyword = whether_r18  # 是否r18
        self.api_0_realnum = 0
        self.api_1_realnum = 0
        self.api_pixiv_realnum = 0
        self.api1_toget_num = 0
        self.api_pixiv_toget_num = 0
        self.db_config = {}

    def build_msg(self, title, artworkid, author, artistid, page, url_original):
        if self.db_config['setuinfoLevel'] == 0:
            msg = ''
        elif self.db_config['setuinfoLevel'] == 1:
            msg = '作品id:{}\r\n作者id:{}\r\nP:{}'.format(artworkid, artistid, page)
        elif self.db_config['setuinfoLevel'] == 2:
            msg = '作品:{}\r\n作者:{}\r\nP:{}\r\n原图:{}'.format(
                'www.pixiv.net/artworks/' + str(artworkid),
                'www.pixiv.net/users/' + str(artistid),
                page,
                url_original
            )
        elif self.db_config['setuinfoLevel'] == 3:
            msg = '标题:{title}\r\n{purl}\r\npage:{page}\r\n作者:{author}\r\n{uurl}\r\n原图:{url_original}'.format(
                title=title,
                purl='www.pixiv.net/artworks/' + str(artworkid),
                page=page,
                author=author,
                uurl='www.pixiv.net/users/' + str(artistid),
                url_original=url_original
            )
        else:
            msg = 'msg配置错误,请联系管理员'
            return msg
        if self.db_config['showTag'] and len(self.tag) >= 1:  # 显示tag
            msg += '\r\nTAG:{}'.format(self.tag)
        if self.db_config['type'] == 'group':
            if self.db_config['revoke']:  # 群聊并且开启撤回
                msg += '\r\nREVOKE[{}]'.format(self.db_config['revoke'])
            if self.db_config['at']:
                return '\r\n' + msg
        return msg

    def base_64(self, path):
        try:
            with open(path, 'rb') as f:
                code = base64.b64encode(f.read()).decode()  # 读取文件内容，转换为base64编码
                logger.info('本地base64转码~')
                return code
        except:
            logger.error('路径{} ,base64转码出错,检查图片路径~'.format(path))
            return

    def if_sent(self, url):  # 判断是否发送过
        filename = os.path.basename(url)
        if data := db_tmp.table('sentlist').search(
                (Q['id'] == self.db_config['callid']) & (Q['filename'] == filename)):  # 如果有数据
            if time.time() - data[0]['time'] <= self.db_config['clearSentTime']:  # 发送过
                logger.info('id:{},{}发送过~'.format(self.db_config['callid'], filename))
                return True
            else:
                db_tmp.table('sentlist').update({'time': time.time()},
                                                (Q['id'] == self.db_config['callid']) & (Q['filename'] == filename))
                return False
        else:  # 没数据
            db_tmp.table('sentlist').insert({'id': self.db_config['callid'], 'time': time.time(), 'filename': filename})
            return False

    def api_0(self):
        url = 'http://api.yuban10703.xyz:2333/setu_v4'
        params = {'level': self.setu_level,
                  'num': self.num,
                  'tag': self.tag}
        if self.num > 10:  # api限制不能大于10
            params['num'] = 10
        try:
            res = requests.get(url, params, timeout=5)
            setu_data = res.json()
        except Exception as e:
            logger.warning('api0 boom~')
            logger.warning(e)
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    filename = data['filename']
                    if self.if_sent(data['original']):  # 判断是否发送过
                        continue
                    url_original = data['original']
                    msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'],
                                         data['page'], url_original)
                    if config['path'] == '':
                        if self.db_config['original']:
                            sendMsg.send_pic(self.ctx, msg, url_original, False, self.db_config['at'])
                        else:
                            sendMsg.send_pic(self.ctx, msg, data['large'],
                                             False, self.db_config['at'])
                    else:  # 本地base64
                        sendMsg.send_pic(self.ctx, msg, '', False, self.db_config['at'],
                                         self.base_64(config['path'] + filename))
                    self.api_0_realnum += 1
                # else:
                #     logger.warning('api0:{}'.format(res.status_code))
            logger.info(
                '从yubanのapi获取到{}张setu  实际发送{}张'.format(setu_data['count'], self.api_0_realnum))  # 打印获取到多少条

    def api_1(self):
        self.api1_toget_num = self.num - self.api_0_realnum
        if self.api1_toget_num > 10:
            self.api1_toget_num = 10
        # 兼容api0
        if self.api1_toget_num <= 0:
            return
        if self.setu_level == 1:
            r18 = 0
        elif self.setu_level == 3:
            r18 = random.choice([0, 1])
        elif self.setu_level == 2:
            r18 = 1
        else:
            r18 = 0
        url = 'https://api.lolicon.app/setu'
        params = {'r18': r18,
                  'apikey': config['lolicon_API_Key'],
                  'num': self.api1_toget_num,
                  'size1200': not bool(self.db_config['original'])}
        if len(self.tag) != 1 or (len(self.tag[0]) != 0 and not self.tag[0].isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            params['keyword'] = self.tag
        if not bool(config['proxy']):  # 不开启反代
            params['proxy'] = 'disable'
        try:
            res = requests.get(url, params, timeout=8)
            setu_data = res.json()
        except Exception as e:
            logger.warning('api1 boom~')
            logger.warning(e)
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    if self.if_sent(data['url']):  # 判断是否发送过
                        continue
                    msg = self.build_msg(data['title'], data['pid'], data['author'], data['uid'], data['p'], '无~')
                    sendMsg.send_pic(self.ctx, msg, data['url'], False, self.db_config['at'])
                    self.api_1_realnum += 1
                logger.info(
                    '从loliconのapi获取到{}张setu  实际发送{}张'.format(setu_data['count'], self.api_1_realnum))  # 打印获取到多少条
            else:
                logger.warning('api1:{}'.format(res.status_code))

    def api_pixiv(self):  # p站热度榜
        self.api_pixiv_toget_num = self.num - self.api_0_realnum - self.api_1_realnum
        if self.api_pixiv_toget_num <= 0:
            return
        if self.setu_level == 2:
            self.tag.append('R-18')
        url = 'https://app-api.pixiv.net/v1/search/popular-preview/illust'
        hash_secret = '28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c'
        X_Client_Time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+08:00')
        X_Client_Hash = hashlib.md5((X_Client_Time + hash_secret).encode('utf-8')).hexdigest()
        headers = {'Authorization': 'Bearer {}'.format(pixivid['access_token']),
                   'User-Agent': 'PixivAndroidApp/5.0.197 (Android 10; Redmi 4)',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept-Language': 'zh_CN_#Hans',
                   'App-OS': 'android',
                   'App-OS-Version': '10',
                   'App-Version': '5.0.197',
                   'X-Client-Time': X_Client_Time,
                   'X-Client-Hash': X_Client_Hash,
                   'Host': 'app-api.pixiv.net',
                   'Accept-Encoding': 'gzip'}
        params = {'filter': 'for_android',
                  'include_translated_tag_results': 'true',
                  'merge_plain_keyword_results': 'true',
                  'word': ' '.join(self.tag),
                  'search_target': 'partial_match_for_tags'}  # 精确:exact_match_for_tags,部分:partial_match_for_tags
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
        except Exception as e:
            logger.warning('Pixiv热度榜获取失败~')
            logger.warning(e)
        else:
            if res.status_code == 200:
                for setu in data['illusts']:
                    if self.api_pixiv_realnum == self.api_pixiv_toget_num:
                        break
                    if setu['page_count'] != 1:  # 多页画廊
                        continue
                    if setu['x_restrict'] == 2:  # R18G
                        continue
                    if self.setu_level in [0, 1] and setu['x_restrict'] == 1:  # R18
                        continue
                    if self.if_sent(setu['meta_single_page']['original_image_url']):  # 判断是否发送过
                        continue
                    msg = self.build_msg(setu['title'], setu['id'], setu['user']['name'], setu['user']['id'], 1, '无~~')
                    if self.db_config['original']:  # 原图
                        sendMsg.send_pic(self.ctx, msg, setu['meta_single_page']['original_image_url'], False,
                                         self.db_config['at'])
                    else:  # 非原图都是webp格式,pcqq不显示,转换格式用base64发送
                        buffer = io.BytesIO()
                        img_webp = requests.get(setu['image_urls']['large'],
                                                headers={'Referer': 'https://www.pixiv.net'}).content  # 下载图片
                        Image.open(io.BytesIO(img_webp)).save(buffer, format='png')  # 转换格式
                        b64code = base64.b64encode(buffer.getvalue()).decode()
                        sendMsg.send_pic(self.ctx, msg, '', False, self.db_config['at'], b64code)
                    self.api_pixiv_realnum += 1
                logger.info(
                    '从Pixiv热度榜获取到{}张setu  实际发送{}张'.format(len(data['illusts']), self.api_pixiv_realnum))  # 打印获取到多少条
            else:
                logger.warning('Pixiv热度榜:{},{}'.format(res.status_code, res.json()))

    def _freq(func):
        def wrapper(self, *args, **kwargs):
            if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
                # ------------------------------------------------------------------------
                if data_tmp := db_tmp.table('freq').search(Q['group'] == self.ctx.FromGroupId):  # 如果有数据
                    if self.db_config['refreshTime'] != 0 and (
                            time.time() - data_tmp[0]['time'] >= self.db_config['refreshTime']):  # 刷新
                        db_tmp.table('freq').update({'time': time.time(), 'freq': 0},
                                                    Q['group'] == self.ctx.FromGroupId)
                    elif self.db_config['freq'] != 0 and self.num + data_tmp[0]['freq'] > self.db_config[
                        'freq']:  # 大于限制且不为0
                        logger.info('群:{}大于频率限制:{}次/{}s'.format(self.ctx.FromGroupId, self.db_config['freq'],
                                                                self.db_config['refreshTime']))
                        msg = self.db_config['msg_frequency'].format(
                            time=self.db_config['refreshTime'],
                            num=self.db_config['freq'],
                            num_call=data_tmp[0]['freq'],
                            r_time=round(self.db_config['refreshTime'] - (time.time() - data_tmp[0]['time']))
                        )
                        sendMsg.send_text(self.ctx, msg, self.db_config['at_warning'])
                        return
                    # 记录
                    db_tmp.table('freq').update(add('freq', self.num), Q['group'] == self.ctx.FromGroupId)
                else:  # 没数据
                    logger.info('群:{}第一次调用'.format(self.ctx.FromGroupId))
                    db_tmp.table('freq').insert(
                        {'group': self.ctx.FromGroupId, 'time': time.time(), 'freq': self.num})
            func(self, *args, **kwargs)

        return wrapper

    def processing_and_inspect(self):  # 处理消息+调用
        # -----------------------------------------------
        if self.num != '':  # 如果指定了数量
            try:
                self.num = int(self.num)
            except:  # 出错就说明不是数字
                sendMsg.send_text(self.ctx, self.db_config['msg_inputError'], self.db_config['at_warning'])
                return
            if self.num <= 0:  # ?????
                sendMsg.send_text(self.ctx, self.db_config['msg_lessThan0'], self.db_config['at_warning'])
                return
        else:  # 未指定默认1
            self.num = 1
        # -----------------------------------------------
        self.setu_level = self.db_config['setuDefaultLevel']  # 默认色图等级
        # -----------------------------------------------
        if self.db_config['type'] in ['group', 'temp']:
            if not self.db_config['setu']:
                sendMsg.send_text(self.ctx, self.db_config['msg_setuClosed'], self.db_config['at_warning'])
                return
            if self.num > self.db_config['maxnum']:
                sendMsg.send_text(self.ctx, self.db_config['msg_tooMuch'], self.db_config['at_warning'])
                return
            if self.r18_OnOff_keyword != '':
                if self.db_config['r18']:
                    self.setu_level = 2
                else:
                    sendMsg.send_text(self.ctx, self.db_config['msg_r18Closed'], self.db_config['at_warning'])
                    return
        elif self.db_config['type'] == 'friend':
            if self.r18_OnOff_keyword != '':
                self.setu_level = 2
        self.send()

    def group_or_temp(self):  # 读数据库+鉴权+判断开关
        if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
            # groupid = self.ctx.FromGroupId
            self.db_config['type'] = 'group'
            self.db_config['callqq'] = self.ctx.FromUserId
            self.db_config['callid'] = self.ctx.FromGroupId
        elif self.ctx.MsgType == 'TempSessionMsg':  # 临时会话
            # groupid = self.ctx.TempUin
            self.db_config['callqq'] = self.ctx.FromUin
            self.db_config['callid'] = self.ctx.TempUin
            self.db_config['type'] = 'temp'
        if data := group_config.search(Q['GroupId'] == self.db_config['callid']):  # 查询group数据库数据
            for key, value in data[0].items():
                if type(value) == dict and key != 'MsgCount':
                    self.db_config[key] = value[self.db_config['type']]
                    continue
                self.db_config[key] = value
            # self.tag = TagMapping().replace_tags(self.db_config['callid'], self.db_config['callqq'], self.tag)  # 替换tag
            self.processing_and_inspect()
        else:
            sendMsg.send_text(self.ctx, '数据库无群:{}信息,请联系管理员~'.format(self.db_config['callid']))
            logger.error('数据库无群:{}信息'.format(self.db_config['callid']))
            return

    def friend(self):
        self.db_config['type'] = 'friend'
        self.db_config['callqq'] = self.ctx.FromUin
        self.db_config['callid'] = self.ctx.FromUin
        if data := friend_config.search(Q['QQ'] == self.ctx.FromUin):  # 该QQ如果自定义过
            self.db_config.update(data[0])
            self.processing_and_inspect()
        else:  # 如果没有自定义 就是默认行为
            # pass#todo:friend数据库待完善
            self.db_config.update({
                'setuinfoLevel': 3,
                'original': False,
                'setuDefaultLevel': 1,
                'clearSentTime': 600,
                'at': False,
                'at_warning': False,  # @
                'showTag': True,
                'msg_inputError': '必须是正整数数字哦~',  # 非int
                'msg_notFind': '你的xp好奇怪啊',  # 没结果
                'msg_tooMuch': '爪巴',  # 大于最大值
                'msg_lessThan0': '¿¿¿',  # 小于0
                'msg_setuClosed': 'setu已关闭~',
                'msg_r18Closed': '未开启r18~',
                'msg_insufficient': '关于{tag}的图片只获取到{num}张'
            })
            self.processing_and_inspect()

    def main(self):  # 判断消息类型给对应函数处理
        if self.ctx.__class__.__name__ == 'GroupMsg' or self.ctx.MsgType == 'TempSessionMsg':  # 群聊or临时会话
            self.group_or_temp()
        else:  # 好友会话
            self.friend()

    @_freq  # 频率
    def send(self):  # 判断数量
        self.api_0()
        if len(self.tag) in [0, 1]:
            self.api_1()
        if config['pixiv_api'] and len(self.tag) != 0:
            self.api_pixiv()
        if self.api_0_realnum == 0 and self.api_1_realnum == 0 and self.api_pixiv_realnum == 0:
            sendMsg.send_text(self.ctx, self.db_config['msg_notFind'], self.db_config['at_warning'])
            return
        if self.api_pixiv_realnum < self.api_pixiv_toget_num:
            sendMsg.send_text(self.ctx, self.db_config['msg_insufficient'].format(
                tag=self.tag,
                num=self.api_0_realnum + self.api_1_realnum + self.api_pixiv_realnum
            ), self.db_config['at_warning'])


# todo:修改tag函数完善
class TagMapping:
    def __init__(self, groupid, qqid, userid, tag, mapping):
        self.groupid = groupid
        self.qqid = qqid
        self.userid = userid
        self.tag = list(set(re.split(r',|，|\.|-| |_|/|\\', tag)))  # 分割+去重
        self.mapping = list(set(re.split(r',|，|\.|-| |_|/|\\', mapping)))  # 分割+去重

    def _build_change_msg(self, data, db, docid):  # 原data ,和修改后返回的docid
        original = '{}--{}'.format(data['tag'], data['mapping'])
        nowdata = db.get(doc_id=docid)
        now = '{}--{}'.format(nowdata['tag'], nowdata['mapping'])
        msg = '{}\r\n{}\r\n{}'.format(original, '*' * 8, now)
        return msg

    def addTag_Group(self, groupid: int, userid: int, typ: str, tag: str, mapping: list):
        db = tagdb.table('group')
        if data := db.search((Q['tag'] == tag) & (Q['group'] == groupid)):  # 有数据
            docid = db.update(
                {
                    'time': int(time.time()),
                    'user': userid,
                    'type': typ,
                    'mapping': list(set(mapping + data[0]['mapping']))  # 去重
                },
                (Q['tag'] == tag) & (Q['group'] == groupid)
            )
            msg = self._build_change_msg(data[0], db, docid[0])
        else:
            docid = db.insert(
                {
                    'group': groupid,
                    'user': userid,
                    'time': int(time.time()),
                    'type': typ,
                    'delete': False,
                    'tag': tag,
                    'mapping': list(set(mapping))
                }
            )
            data = db.get(doc_id=docid)
            msg = '{}--{}'.format(data['tag'], data['mapping'])
        return msg

    def addTag_Ind(self, groupid: int, qqid: int, userid: int, typ: str, tag: str, mapping: list):
        db = tagdb.table('exception')
        if data := db.search((Q['tag'] == tag) & (Q['group'] == groupid) & (Q['qqid'] == qqid)):  # 有数据
            docid = db.update(
                {
                    'time': int(time.time()),
                    'user': userid,
                    'type': typ,
                    'mapping': list(set(mapping + data[0]['mapping']))  # 去重
                },
                (Q['tag'] == tag) & (Q['group'] == groupid & (Q['qqid'] == qqid))
            )
            msg = self._build_change_msg(data[0], db, docid[0])
        else:
            docid = db.insert(
                {
                    'group': groupid,
                    'qqid': qqid,
                    'user': userid,
                    'time': int(time.time()),
                    'type': typ,
                    'delete': False,
                    'tag': tag,
                    'mapping': list(set(mapping))
                }
            )
            data = db.get(doc_id=docid)
            msg = '{}--{}'.format(data['tag'], data['mapping'])
        return msg

    def delTag_Group(self, tag: str, deltag: list):
        db = tagdb.table('group')
        if data := db.search((Q['tag'] == tag) & (Q['group'] == self.groupid)):  # 有数据
            data_tmp = data.copy()[0]  # 复制一份,做对比
            failtag = []
            for tag_d in deltag:
                try:
                    data_tmp['mapping'].remove(tag_d)
                except:
                    failtag.append(tag_d)
            docid = db.update(
                {
                    'time': int(time.time()),
                    'user': self.userid,
                    'mapping': data_tmp['mapping']
                },
                (Q['tag'] == tag) & (Q['group'] == self.groupid)
            )
            msg = self._build_change_msg(data[0], db, docid[0])
            if failtag:
                return msg + '\r\nTAG:{}删除失败'.format(failtag)
            return msg
        else:
            return '无TAG:{}'.format(tag)

    def del_tag_group(self, tag):
        db = tagdb.table('group')

        pass

    def del_tag_someone(self, tag):
        db = tagdb.table('exception')

        pass

    # def delTag_Ind(self, tag: str, deltag: list):
    #     db = tagdb.table('exception')
    #     if data := db.search((Q['tag'] == tag) & (Q['group'] == groupid) & (Q['qqid'] == qqid)):  # 有数据
    #         data_tmp = data.copy()[0]  # 复制一份,做对比
    #         failtag = []
    #         for tag_d in deltag:
    #             try:
    #                 data_tmp['mapping'].remove(tag_d)
    #             except:
    #                 failtag.append(tag_d)
    #         docid = db.update(
    #             {
    #                 'time': int(time.time()),
    #                 'user': self.userid,
    #                 'mapping': data_tmp['mapping']
    #             },
    #             (Q['tag'] == tag) & (Q['group'] == self.groupid & (Q['qqid'] == self.qqid))
    #         )
    #         msg = self._build_change_msg(data[0], db, docid[0])
    #         if failtag:
    #             return msg + '\r\nTAG:{}删除失败'.format(failtag)
    #         return msg
    #     else:
    #         return '无TAG:{}'.format(tag)

    def replace_tags(self, groupid: int, qqid: int, tags: list):
        tags_mapping = []
        for tag in tags:
            if data := tagdb.table('exception').search(
                    (Q['tag'] == tag) & (Q['group'] == groupid) & (Q['qqid'] == qqid)):  # 给单独用户的映射 有数据
                pass
            elif data := tagdb.table('group').search((Q['tag'] == tag) & (Q['group'] == groupid)):  # 群的映射 有数据
                pass
            else:
                tags_mapping.append(tag)
                continue
            if data[0]['type'] == 'random':
                tags_mapping.append(random.choice(data[0]['mapping']))
            else:  # 'type': 'all'
                tags_mapping += data[0]['mapping']
        return tags_mapping

    def get_group_tag(self):
        pass

    def group(self, typ):
        db = tagdb.table('group')
        msg_full = ''
        for tag in self.tag:
            if data := db.search((Q['tag'] == tag) & (Q['group'] == self.groupid)):  # 有数据
                docid = db.update(
                    {
                        'time': int(time.time()),
                        'user': self.userid,
                        'type': typ,
                        'mapping': list(set(self.mapping + data[0]['mapping']))  # 去重
                    },
                    (Q['tag'] == tag) & (Q['group'] == self.groupid)
                )
                msg_full += (self._build_change_msg(data[0], db, docid[0]) + '\r\n')
            else:
                docid = db.insert(
                    {
                        'group': self.groupid,
                        'user': self.userid,
                        'time': int(time.time()),
                        'type': typ,
                        'delete': False,
                        'tag': tag,
                        'mapping': list(set(self.mapping))
                    }
                )
                data = db.get(doc_id=docid)
                msg_full += '{}--{}'.format(data['tag'], data['mapping'])
        return msg_full

    def group_someone(self, typ):
        db = tagdb.table('exception')
        msg_full = ''
        for tag in self.tag:
            if data := db.search((Q['tag'] == tag) & (Q['group'] == self.groupid) & (Q['qqid'] == self.qqid)):  # 有数据
                docid = db.update(
                    {
                        'time': int(time.time()),
                        'user': self.userid,
                        'type': typ,
                        'mapping': list(set(self.mapping + data[0]['mapping']))  # 去重
                    },
                    (Q['tag'] == tag) & (Q['group'] == self.groupid & (Q['qqid'] == self.qqid))
                )
                msg_full += (self._build_change_msg(data[0], db, docid[0]) + '\r\n')
            else:
                docid = db.insert(
                    {
                        'group': self.groupid,
                        'qqid': self.qqid,
                        'user': self.userid,
                        'time': int(time.time()),
                        'type': typ,
                        'delete': False,
                        'tag': tag,
                        'mapping': list(set(self.mapping))
                    }
                )
                data = db.get(doc_id=docid)
                msg_full = '{}--{}'.format(data['tag'], data['mapping'])
        return msg_full


class Getdata:
    def defaultdata(self, data):
        data['managers'] = []  # 所有的管理者(可以设置bot功能的)
        # -----------------------------------------------------
        data['setuDefaultLevel'] = {'group': 1, 'temp': 3}  # 默认等级 0:正常 1:性感 2:色情 3:All
        data['setuinfoLevel'] = {'group': 1, 'temp': 3}  # setu信息完整度(0:不显示图片信息)
        data['original'] = {'group': False, 'temp': False}  # 是否原图
        data['setu'] = {'group': True, 'temp': True}  # 色图功能开关
        data['r18'] = {'group': False, 'temp': True}  # 是否开启r18
        data['freq'] = 10  # 频率 (次)
        data['refreshTime'] = 60  # 刷新时间 (s)
        data['clearSentTime'] = 900  # 刷新sent时间 (s)
        data['maxnum'] = {'group': 3, 'temp': 10}  # 一次最多数量
        # data['MsgCount'] = {'text': 0, 'pic': 0, 'voice': 0}  # 消息数量
        data['revoke'] = {'group': 20, 'temp': 0}  # 撤回消息延时(0为不撤回)
        data['at'] = False  # @
        data['at_warning'] = False  # @
        data['showTag'] = True  # 显示tag
        data['msg_inputError'] = '必须是正整数数字哦~'  # 非int
        data['msg_notFind'] = '你的xp好奇怪啊'  # 没结果
        data['msg_tooMuch'] = '爪巴'  # 大于最大值
        data['msg_lessThan0'] = '¿¿¿'  # 小于0
        data['msg_setuClosed'] = 'setu已关闭~'
        data['msg_r18Closed'] = '未开启r18~'
        data['msg_insufficient'] = '关于{tag}的图片只获取到{num}张'
        data['msg_frequency'] = '本群每{time}s能调用{num}次,已经调用{num_call}次,离刷新还有{r_time}s'
        # data['msg_'] = ''
        # return data

    def _updateData(self, data, groupid):
        if group_config.search(Q['GroupId'] == groupid):
            logger.info('群:{}已存在,更新数据~'.format(groupid))
            group_config.update(data, Q['GroupId'] == groupid)
        else:
            self.defaultdata(data)
            logger.info('群:{}不存在,插入数据~'.format(groupid))
            group_config.insert(data)

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateAllGroupData(self):
        logger.info('开始更新所有群数据~')
        data = action.get_group_list()['TroopList']
        allgroups_get = [x['GroupId'] for x in data]
        for group in data:
            del group['GroupNotice']  # 删除不需要的key
            admins = action.get_group_all_admin_list(group['GroupId'])
            admins_QQid = [i['MemberUin'] for i in admins]
            group['admins'] = admins_QQid  # 管理员列表
            self._updateData(group, group['GroupId'])
        allgroups_db = [i['GroupId'] for i in group_config.all()]
        if extraGroup := list(set(allgroups_db).difference(set(allgroups_get))):  # 多余的群
            logger.info('数据库中多余群:{}'.format(extraGroup))
            for groupid_del in extraGroup:
                group_config.remove(Q['GroupId'] == groupid_del)
                logger.info('已删除群:{}数据'.format(groupid_del))
        logger.success('更新群信息成功~')
        return

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateGroupData(self, groupid: int):
        logger.info('开始刷新群:{}的数据'.format(groupid))
        data = action.get_group_list()['TroopList']
        for group in data:
            if group['GroupId'] == groupid:
                del group['GroupNotice']  # 删除不需要的key
                admins = action.get_group_all_admin_list(groupid)
                admins_QQid = [i['MemberUin'] for i in admins]
                group['admins'] = admins_QQid
                logger.info('群:{}的admins:{}'.format(groupid, admins_QQid))
                self._updateData(group, group['GroupId'])
                return
        logger.warning('群:{}不存在~'.format(groupid))


botdata = Getdata()


# todo:命令待完善 加log
class Command:
    def __init__(self, ctx):
        self.ctx = ctx
        self.db_raw = {}  # 原始数据库
        self.db = {}

    def change_dict(self, dicta, lista, change, ret=''):
        x = dicta[lista[0]]
        ret += (str(lista[0]) + ' ')
        if len(lista) == 1:
            rt_befeore = dicta.copy()
            dicta[lista[0]] = change
            return '{}: {}\n↓↓↓↓\n{}: {}'.format(ret, rt_befeore[lista[0]], ret, dicta[lista[0]])
        lista.pop(0)
        return self.change_dict(x, lista, change, ret)

    def cmd_group(self, lv):  # 2<1<0   0:root
        if lv == 0:  # todo:封装成函数
            if cmd := re.match('_cmd (.*) (.*):(.*)', self.ctx.Content):  # 万能修改
                keys = cmd[1].split()
                data_type = cmd[2]
                if data_type == 'int':
                    data = int(cmd[3])
                elif data_type == 'bool':
                    data = bool(int(cmd[3]))
                elif data_type == 'str':
                    data = str(cmd[3])
                else:
                    sendMsg.send_text(self.ctx, 'error')
                    return
                try:
                    ret = self.change_dict(self.db_raw, keys, data)
                except:
                    sendMsg.send_text(self.ctx, 'ERROR')
                    return
        if lv <= 1:
            if self.ctx.MsgType == 'AtMsg':
                At_Content_front = re.sub(r'@.*', '', json.loads(self.ctx.Content)['Content'])  # @消息前面的内容
                atqqs: list = json.loads(self.ctx.Content)['UserID']
                if At_Content_front == '_增加管理员':
                    for qq in atqqs:
                        if qq in self.db['admins']:
                            sendMsg.send_text(self.ctx, '{}已经是管理员了'.format(qq))
                            sendMsg.send_text(self.ctx, '增加管理员失败')
                            return
                        self.db['managers'].append(qq)
                    ret = '增加管理员成功'

                elif At_Content_front == '_删除管理员':
                    for qq in atqqs:
                        try:
                            self.db['managers'].remove(qq)
                        except:
                            sendMsg.send_text(self.ctx, '删除管理员出错')
                            return
                    ret = '删除管理员成功'
        if lv <= 2:
            if self.ctx.Content == '_开启群聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'group'], True)
            elif self.ctx.Content == '_关闭群聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'group'], False)
            elif self.ctx.Content == '_开启私聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'temp'], True)
            elif self.ctx.Content == '_关闭私聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'temp'], False)
            elif self.ctx.Content == '_开启私聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'temp'], True)
            elif self.ctx.Content == '_关闭私聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'temp'], False)
            elif self.ctx.Content == '_开启群聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'group'], True)
            elif self.ctx.Content == '_关闭群聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'group'], False)
            elif self.ctx.Content == '_关闭群聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'group'], 0)
            elif self.ctx.Content == '_开启群聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'group'], 25)  # 默认开启撤回为25s
            elif self.ctx.Content == '_关闭私聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'temp'], 0)
            elif self.ctx.Content == '_开启私聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'temp'], 25)  # 默认开启撤回为25s
            elif self.ctx.Content == '_开启群聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'group'], True)
            elif self.ctx.Content == '_关闭群聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'group'], False)
            elif self.ctx.Content == '_开启私聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'temp'], True)
            elif self.ctx.Content == '_关闭私聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'temp'], False)
            elif self.ctx.Content == '_开启色图@':
                ret = self.change_dict(self.db_raw, ['at'], True)
            elif self.ctx.Content == '_关闭色图@':
                ret = self.change_dict(self.db_raw, ['at'], False)
            elif self.ctx.Content == '_开启警告@':
                ret = self.change_dict(self.db_raw, ['at_warning'], True)
            elif self.ctx.Content == '_关闭警告@':
                ret = self.change_dict(self.db_raw, ['at_warning'], False)
            elif self.ctx.Content == '_开启tag显示':
                ret = self.change_dict(self.db_raw, ['showTag'], True)
            elif self.ctx.Content == '_关闭tag显示':
                ret = self.change_dict(self.db_raw, ['showTag'], False)
            elif info := re.match('_修改频率 (\d+)\/(\d+)', self.ctx.Content):  # 次数/时间
                ret_0 = self.change_dict(self.db_raw, ['freq'], int(info[1]))
                ret_1 = self.change_dict(self.db_raw, ['refreshTime'], int(info[2]))
                ret = ret_0 + '\n------\n' + ret_1
            elif info := re.match('_修改重复发送间隔 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['clearSentTime'], int(info[1]))
            elif info := re.match('_修改群聊单次最大值 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['maxnum', 'group'], int(info[1]))
            elif info := re.match('_修改私聊单次最大值 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['maxnum', 'temp'], int(info[1]))
            elif info := re.match('_修改群聊撤回时间 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['revoke', 'group'], int(info[1]))
            elif info := re.match('_修改私聊撤回时间 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['revoke', 'temp'], int(info[1]))
            elif info := re.match('_修改群聊setu信息等级 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['setuinfoLevel', 'group'], int(info[1]))
            elif info := re.match('_修改私聊setu信息等级 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['setuinfoLevel', 'temp'], int(info[1]))
            elif info := re.match('_修改群聊setu默认等级 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['setuDefaultLevel', 'group'], int(info[1]))
            elif info := re.match('_修改私聊setu默认等级 (\d+)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['setuDefaultLevel', 'temp'], int(info[1]))
            elif info := re.match('_修改输入错误回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_inputError'], str(info[1]))
            elif info := re.match('_修改没找到的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_notFind'], str(info[1]))
            elif info := re.match('_修改获取过多的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_tooMuch'], str(info[1]))
            elif info := re.match('_修改获取小于0的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_lessThan0'], str(info[1]))
            elif info := re.match('_修改结果不够的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_insufficient'], str(info[1]))
            elif info := re.match('_修改已关闭色图的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_setuClosed'], str(info[1]))
            elif info := re.match('_修改已关闭r18的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_r18Closed'], str(info[1]))
            elif info := re.match('_修改达到频率限制的回复 (.*)', self.ctx.Content):
                ret = self.change_dict(self.db_raw, ['msg_frequency'], str(info[1]))
        if 'ret' in locals().keys():  # 如果有ret
            sendMsg.send_text(self.ctx, ret)
            group_config.update(self.db_raw, Q['GroupId'] == self.db['GroupId'])
        else:
            sendMsg.send_text(self.ctx, '未匹配到命令')

    def group_or_temp(self):  # todo: 命令分层
        if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
            groupid = self.ctx.FromGroupId
            self.db['type'] = 'group'
            self.db['callqq'] = self.ctx.FromUserId
        elif self.ctx.MsgType == 'TempSessionMsg':  # 临时会话
            groupid = self.ctx.TempUin
            self.db['callqq'] = self.ctx.FromUin
            self.db['type'] = 'temp'
        if data := group_config.search(Q['GroupId'] == groupid):  # 查询group数据库数据
            self.db_raw = data[0]
            self.db.update(data[0])  # 载入数据
            # -------------------权限等级分层-----------------------------------
            if self.db['callqq'] == config['superAdmin']:  # 鉴权(等级高的写前面)
                lv = 0
            elif self.db['callqq'] in data[0]['admins']:
                lv = 1
            elif self.db['callqq'] in data[0]['managers']:
                lv = 2
            else:
                sendMsg.send_text(self.ctx, '你没有权限,爪巴', True)
                return
            self.cmd_group(lv)
            logger.info('callqq:{}  等级{})'.format(self.db['callqq'], lv))
        else:
            sendMsg.send_text(self.ctx, '数据库无群:{}信息,请联系管理员~'.format(groupid))
            logger.error('数据库无群:{}信息'.format(groupid))
            return

    def friend(self):
        pass

    def cmd_friend(self, lv):  # todo:superadmin万能修改
        pass

    def main(self):
        if self.ctx.__class__.__name__ == 'GroupMsg' or self.ctx.MsgType == 'TempSessionMsg':  # 群聊or临时会话
            self.group_or_temp()
        else:  # 好友会话
            self.friend()


# ----------------------------------------------------------------------

@bot.on_group_msg
@deco.in_content(pattern_setu)
def group_setu(ctx: GroupMsg):
    info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    Setu(ctx, info[2], info[1], info[3]).main()


@bot.on_friend_msg
@deco.in_content(pattern_setu)
def friend_setu(ctx: FriendMsg):
    info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    Setu(ctx, info[2], info[1], info[3]).main()


# ----------------------------------------------------------------------


@bot.on_group_msg
@deco.not_botself
@deco.in_content('\_.*')
@deco.only_this_msg_type('TextMsg')
def group_cmd(ctx: GroupMsg):
    Command(ctx).main()


@bot.on_group_msg
@deco.not_botself
@deco.in_content('\_.*')
@deco.only_this_msg_type('AtMsg')
def group_cmd(ctx: GroupMsg):
    Command(ctx).main()


# @bot.on_group_msg
# @deco.in_content(r'(.*)--(.*)')
# @deco.only_this_msg_type('TextMsg')
# def tag_group(ctx: GroupMsg):
#     info = re.search(r'(.*)--(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(ctx.FromGroupId, 0, ctx.FromUserId, info[1], info[2]).group('random')
#     sendMsg.send_text(ctx, msg)


# @bot.on_group_msg
# @deco.in_content('(.*)==(.*)')
# @deco.only_this_msg_type('TextMsg')
# def tag_group(ctx: GroupMsg):
#     info = re.search('(.*)==(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(ctx.FromGroupId, 0, ctx.FromUserId, info[1], info[2]).group('all')
#     sendMsg.send_text(ctx, msg)


# # -----------------------------------------------------------------------

# @bot.on_friend_msg
# @deco.in_content('[Gg][:：](\d+)[，,](.*)--(.*)')
# @deco.only_this_msg_type('TextMsg')  # todo 判断会话
# def tag_group(ctx: FriendMsg):
#     info = re.search('[Gg][:：](\d+)[，,](.*)--(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(info[1], 0, ctx.FromUin, info[2], info[3]).group('random')
#     sendMsg.send_text(ctx, msg)


# @bot.on_friend_msg
# @deco.in_content('[Gg][:：](\d+)[，,](.*)==(.*)')
# @deco.only_this_msg_type('TextMsg')
# def tag_group(ctx: FriendMsg):
#     info = re.search('[Gg][:：](\d+)[，,](.*)==(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(info[1], 0, ctx.FromUin, info[2], info[3]).group('all')
#     sendMsg.send_text(ctx, msg)


# @bot.on_friend_msg
# @deco.in_content('[Gg][:：](\d+) [Qq][:：](\d+)[，,](.*)--(.*)')
# @deco.only_this_msg_type('TextMsg')
# def tag_group(ctx: FriendMsg):
#     info = re.search('[Gg][:：](\d+) [Qq][:：](\d+)[，,](.*)--(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(info[1], info[2], ctx.FromUin, info[3], info[4]).group_someone('random')
#     sendMsg.send_text(ctx, msg)


# @bot.on_friend_msg
# @deco.in_content('[Gg][:：](\d+) [Qq][:：](\d+)[，,](.*)==(.*)')
# @deco.only_this_msg_type('TextMsg')
# def tag_group(ctx: FriendMsg):
#     info = re.search('[Gg][:：](\d+) [Qq][:：](\d+)[，,](.*)==(.*)', ctx.Content)  # 提取关键字
#     msg = TagMapping(info[1], info[2], ctx.FromUin, info[3], info[4]).group_someone('all')
#     sendMsg.send_text(ctx, msg)


@bot.on_event
def event(ctx: EventMsg):
    # print(ctx.message)
    if admin_info := refine_group_admin_event_msg(ctx):
        if data_raw := group_config.search(Q['GroupId'] == admin_info.GroupID):
            if admin_info.Flag == 1:  # 变成管理员
                logger.info('群:{} QQ:{}成为管理员'.format(admin_info.GroupID, admin_info.UserID))
                if admin_info.UserID in data_raw[0]['managers']:  # 防止重叠
                    data_raw[0]['managers'].remove[admin_info.UserID]
                data_raw[0]['admins'].append(admin_info.UserID)
            else:
                logger.info('群:{} QQ:{}被取消管理员'.format(admin_info.GroupID, admin_info.UserID))
                try:
                    data_raw[0]['admins'].remove(admin_info.UserID)
                except:  # 出错就说明群信息不正确,重新获取
                    logger.warning('从数据库删除管理员出错,尝试重新刷新群数据')
                    botdata.updateGroupData(admin_info.GroupID)
                    return
            group_config.update({'admins': data_raw[0]['admins'],
                                 'managers': data_raw[0]['managers']},
                                Q['GroupId'] == admin_info.GroupID)
        else:  # 如果没数据就重新获取
            botdata.updateGroupData(admin_info.GroupID)
    elif join_info := refine_group_join_event_msg(ctx):
        if join_info.UserID == config['botQQ']:
            logger.info('bot加入群{}'.format(join_info.FromUin))
            botdata.updateGroupData(join_info.FromUin)
        else:
            logger.info('{}:{}加入群{}'.format(join_info.UserName, join_info.UserID, join_info.FromUin))
    elif ctx.MsgType == 'ON_EVENT_GROUP_JOIN_SUCC':
        logger.info('bot加入群{}'.format(ctx.FromUin))
        botdata.updateGroupData(ctx.FromUin)


@bot.on_group_msg
@deco.is_botself
@deco.in_content('REVOKE')
def receive_group_msg(ctx: GroupMsg):
    delay = re.findall(r'REVOKE\[(\d+)\]', ctx.Content)
    if delay:
        delay = min(int(delay[0]), 90)
    else:
        delay = random.randint(30, 60)
    time.sleep(delay)

    action.revoke_msg(
        groupid=ctx.FromGroupId, msgseq=ctx.MsgSeq, msgrandom=ctx.MsgRandom
    )


@bot.when_disconnected(every_time=True)
def disconnected():
    logger.warning('socket断开~')


@bot.when_connected(every_time=True)
def connected():
    logger.success('socket连接成功~')
    # botdata.updateAllGroupData()


# todo:tag替换完善 #记录调用tag,做一个排行
if __name__ == '__main__':
    if os.path.isfile('.bot_setu_v3_flag'):  # 有文件
        # pass
        threading.Thread(target=botdata.updateAllGroupData, daemon=True).start()
    else:
        logger.info('第一次启动~')
        botdata.updateAllGroupData()
        pathlib.Path('.bot_setu_v3_flag').touch()  # 创建flag文件
    # ---------------------------------------------------------------------------------
    if config['pixiv_api']:
        pixiv = PixivToken(config['pixiv_username'], config['pixiv_password'])
        if os.path.isfile('.Pixiv_Token.json'):  # 有文件
            try:
                with open('.Pixiv_Token.json', 'r', encoding='utf-8') as f:
                    pixivid = json.loads(f.read())
                    logger.success('Pixiv_Token载入成功~')
            except:
                logger.error('Pixiv_Token载入失败,请删除.Pixiv_Token.json重新启动~')
                sys.exit()
        else:
            logger.info('无Pixiv_Token文件')
            pixivid = pixiv.get_token()
            if pixivid.get('has_error'):
                logger.error('获取失败~\n' + pixivid['errors']['system']['message'])
                sys.exit()
            pixiv.saveToken(pixivid)
        threading.Thread(target=pixiv.if_refresh_token, daemon=True).start()
    else:
        logger.info('未开启pixiv_api')
    # ---------------------------------------------------------------------------------
    bot.run()
