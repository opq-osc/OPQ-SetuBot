import uuid
# import datetime
from retrying import retry
# from module.database import tmpDB
from module.config import pixivUsername, pixivPassword, api_pixiv
import hashlib
import os
import sys
import requests
import json
import time
from loguru import logger
from datetime import datetime
import threading


# import socket
# import socks


# socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 10808)
# socket.socket = socks.socksocket


class Pixiv:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.tokenapi = 'https://oauth.secure.pixiv.net/auth/token'
        self.tokendata = {}

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
                'device_token': uuid.uuid4().hex,
                'get_secure_url': 'true',
                'include_policy': 'true'}
        try:
            self.tokendata = requests.post(url=self.tokenapi, data=data, headers=self.headers()).json()
        except:
            logger.error('获取token出错~')
            return
        self.tokendata['time'] = time.time()  # 记录时间
        return

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def refresh_token(self):
        logger.info('刷新Pixiv_token~')
        data = {'client_id': 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
                'client_secret': 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
                'grant_type': 'refresh_token',
                'refresh_token': self.tokendata['refresh_token'],
                'device_token': self.tokendata['device_token'],
                'get_secure_url': 'true',
                'include_policy': 'true'}
        self.tokendata = requests.post(url=self.tokenapi, data=data, headers=self.headers()).json()
        self.tokendata['time'] = time.time()
        logger.success('刷新token成功~')
        return

    def pixivSearch(self, tag: list, r18: bool):  # p站热度榜
        if r18:
            tag.append('R-18')
        url = 'https://app-api.pixiv.net/v1/search/popular-preview/illust'
        params = {'filter': 'for_android',
                  'include_translated_tag_results': 'true',
                  'merge_plain_keyword_results': 'true',
                  'word': ' '.join(tag),
                  'search_target': 'partial_match_for_tags'}  # 精确:exact_match_for_tags,部分:partial_match_for_tags
        headers = self.headers()
        headers['Host'] = 'app-api.pixiv.net'
        headers['Authorization'] = 'Bearer {}'.format(self.tokendata['access_token'])
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
        except Exception as e:
            logger.warning('Pixiv热度榜获取失败~ :{}'.format(e))
            return
        else:
            if res.status_code == 200:
                return data

    def if_refresh_token(self):
        if api_pixiv:
            if os.path.isfile('.pixivToken.json'):  # 有文件
                try:
                    with open('.pixivToken.json', 'r', encoding='utf-8') as f:
                        self.tokendata = json.loads(f.read())
                        logger.success('pixivToken载入成功~')
                except:
                    logger.error('pixivToken载入失败,请删除pixivToken.json重新启动~')
                    sys.exit()
            else:
                logger.info('无pixivToken文件,尝试获取~')
                self.get_token()
                self.saveToken()
        while api_pixiv:
            if time.time() - self.tokendata['time'] >= int(self.tokendata['expires_in']):  # 刷新
                try:
                    self.refresh_token()
                    self.saveToken()
                except:
                    logger.warning('刷新Pixiv_token出错')
                    time.sleep(10)
            else:
                time.sleep(int(self.tokendata['expires_in']) - (time.time() - self.tokendata['time']))
        logger.warning('未开启pixivapi或循环异常结束')

    # def loadToken(self):
    #     if os.path.isfile('.pixivToken.json'):  # 有文件
    #         try:
    #             with open('.pixivToken.json', 'r', encoding='utf-8') as f:
    #                 self.tokendata = json.loads(f.read())
    #                 logger.success('pixivToken载入成功~')
    #         except:
    #             logger.error('pixivToken载入失败,请删除pixivToken.json重新启动~')
    #             sys.exit()
    #     else:
    #         logger.info('无pixivToken文件,尝试获取~')
    #         self.get_token()

    def saveToken(self):
        with open('.pixivToken.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.tokendata))
        logger.success('PixivToken已保存到.pixivToken.json')
        return


pixiv = Pixiv(pixivUsername, pixivPassword)
threading.Thread(target=pixiv.if_refresh_token, daemon=True).start()
