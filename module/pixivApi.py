import uuid
from retrying import retry
from module.config import api_pixiv
import hashlib
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
    def __init__(self):
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

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def refresh_token(self, refresh_token, device_token):
        url = 'https://oauth.secure.pixiv.net/auth/token'
        logger.info('刷新Pixiv_token~')
        data = {'client_id': 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
                'client_secret': 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'device_token': device_token,
                'get_secure_url': 'true',
                'include_policy': 'true'}
        self.tokendata = requests.post(url, data=data, headers=self.headers()).json()
        self.tokendata['time'] = time.time()
        logger.success('刷新token成功~')
        self.saveToken()
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
            with requests.session() as s:
                res = s.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
        except Exception as e:
            logger.warning('Pixiv热度榜获取失败~ :{}'.format(e))
            return
        else:
            if res.status_code == 200:
                return data
            else:
                logger.warning('Pixiv热度榜异常:{}'.format(res.status_code))

    def saveToken(self):
        with open('.PixivToken.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.tokendata))
        logger.success('PixivToken已保存到.PixivToken.json')
        return

    def refreshThread(self):
        while True:
            if time.time() - self.tokendata['time'] >= int(self.tokendata['expires_in']):  # 刷新
                try:
                    self.refresh_token(self.tokendata['refresh_token'], self.tokendata['device_token'])
                except:
                    logger.warning('刷新Pixiv_token出错')
                    time.sleep(10)
            else:
                logger.info('PixivToken离下次刷新还有{}s'.format(
                    int(self.tokendata['expires_in']) - (time.time() - self.tokendata['time'])))
                time.sleep(int(self.tokendata['expires_in']) - (time.time() - self.tokendata['time']))

    def login_and_refresh(self):
        try:
            with open('.PixivToken.json', 'r', encoding='utf-8') as f:
                self.tokendata = json.loads(f.read())
                logger.success('载入.PixivToken.json成功~')
        except:
            logger.error('.PixivToken.json载入失败,请检查内容并重新启动~')
            return
        if 'time' not in self.tokendata.keys():
            self.refresh_token(self.tokendata['refresh_token'], uuid.uuid4().hex)
        self.refreshThread()

    def main(self):
        if api_pixiv:
            self.login_and_refresh()
        logger.info('未开启Pixivapi~')


pixiv = Pixiv()
threading.Thread(target=pixiv.main, daemon=True).start()
