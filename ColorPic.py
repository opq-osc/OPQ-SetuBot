# coding=utf-8
import socketio
# import json
import requests
import re
import logging
import time

# import socket
'''
Python插件SDK Ver 0.0.2
维护者:enjoy(2435932516)
有问题联系我。
'''

robotqq = ""  # 机器人QQ号
webapi = "http://10.1.1.168:8888"  # Webapi接口 http://127.0.0.1:8888
color_pickey = ''  # 申请地址api.lolicon.app
size1200 = 'true'  # 是否使用 master_1200 缩略图，即长或宽最大为1200px的缩略图，以节省流量或提升加载速度（某些原图的大小可以达到十几MB）

# -----------------------------------------------------
api = webapi + '/v1/LuaApiCaller'
refreshapi = webapi + '/v1/RefreshKeys'
sio = socketio.Client()
# log文件处理
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=0,
                    filename='new.log', filemode='a')


class GMess:
    # QQ群消息类型
    def __init__(self, message1):
        # print(message1)
        self.FromQQG = message1['FromGroupId']  # 来源QQ群
        self.QQGName = message1['FromGroupName']  # 来源QQ群昵称
        self.FromQQ = message1['FromUserId']  # 来源QQ
        self.FromQQName = message1['FromNickName']  # 来源QQ名称
        self.Content = message1['Content']  # 消息内容


class Mess:
    def __init__(self, message1):
        self.FromQQ = message1['ToUin']
        self.ToQQ = message1['FromUin']
        self.Content = message1['Content']
        try:
            self.FromQQG = message1['TempUin']
        except:
            self.FromQQG = 0


# standard Python

# SocketIO Client
# sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# ----------------------------------------------------- 
# Socketio
# ----------------------------------------------------- 
def refreshkey():
    params = {'qq': robotqq}
    res = requests.get(refreshapi, params=params)
    print(res.text)


def send_text(toid, type, msg, groupid, atuser):
    params = {'qq': robotqq,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": type,
            "sendMsgType": "TextMsg",
            "content": msg,
            "groupid": groupid,
            "atUser": atuser}
    requests.post(api, params=params, json=data)


def send_pic(toid, type, msg, groupid, atuser, picurl='', picbase64='', picmd5=''):
    params = {'qq': robotqq,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": type,
            "sendMsgType": "PicMsg",
            "content": msg,
            "groupid": groupid,
            "atUser": atuser,
            "picUrl": picurl,
            "picBase64Buf": picbase64,
            "fileMd5": picmd5}
    requests.post(api, params=params, json=data, timeout=30)
    print(data)


def beat():
    while (1):
        sio.emit('GetWebConn', robotqq)
        time.sleep(60)


def color_pic(r18, keyword=''):
    url = 'https://api.lolicon.app/setu/'
    params = {'r18': r18,
              'apikey': color_pickey,
              'keyword': keyword,
              'size1200': size1200,
              'proxy': 'i.pixiv.cat'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53',
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=8)
        data = res.json()  # 转换成字典
        picurl = data['data'][0]['url']  # 提取图片链接
        author = data['data'][0]['author']  # 提取作者名字
        title = data['data'][0]['title']  # 图片标题
        purl = 'www.pixiv.net/artworks/' + str(data['data'][0]['pid'])  # 拼凑p站链接
        uurl = 'www.pixiv.net/users/' + str(data['data'][0]['uid'])  # 画师的p站链接
        msg = title + '\r\n' + purl + '\r\n' + author + '\r\n' + uurl  # 组合消息
        return msg, picurl
    except IndexError:
        picurl = 'https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/error.jpg'
        return '你的xp好奇怪啊,爪巴', picurl
    except Exception as error:
        print(error)
        picurl = 'https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/error.jpg'
        return '服务器可能挂掉了' + '\r\n' + str(error), picurl  # 出错了就返回固定值.....


@sio.event
def connect():
    print('connected to server')
    sio.emit('GetWebConn', robotqq)  # 取得当前已经登录的QQ链接
    beat()  # 心跳包，保持对服务器的连接


@sio.on('OnGroupMsgs')
def OnGroupMsgs(message):
    ''' 监听群组消息'''
    tmp = message['CurrentPacket']['Data']
    # print(tmp)
    a = GMess(tmp)
    # cm = a.Content.split(' ',3) #分割命令
    '''
    a.FrQQ 消息来源
    a.QQGName 来源QQ群昵称
    a.FromQQG 来源QQ群
    a.FromNickName 来源QQ昵称
    a.Content 消息内容
    '''
    print('群聊:', a.Content)
    keyword = re.match(r'来[点丶张](.*?)的{0,1}色图', a.Content)  # 瞎写的正则
    if keyword:
        keyword = keyword.group(1)
        data = color_pic(0, keyword=keyword)
        msg = data[0]
        picurl = data[1]
        send_text(a.FromQQG, 2, '', 0, a.FromQQ)
        send_pic(a.FromQQG, 2, msg, a.FromQQ, a.FromQQ, picurl)
        print('已发送~')
        return

    # te = re.search(r'\#(.*)', str(a.Content))
    # if te == None:
    #     # print('???')
    #     return


@sio.on('OnFriendMsgs')
def OnFriendMsgs(message):
    ''' 监听好友消息 '''
    tmp = message['CurrentPacket']['Data']
    a = Mess(tmp)
    # print(tmp)
    # cm = a.Content.split(' ')
    print('好友:', a.Content)
    keyword = re.match(r'来[点丶张](.*?)的{0,1}色图', a.Content)  # 瞎写的正则
    if keyword:
        keyword = keyword.group(1)
        data = color_pic(1, keyword=keyword)
        msg = data[0]
        picurl = data[1]
        send_pic(a.ToQQ, 3, msg, a.FromQQG, 0, picurl)
        print('已发送~')
        return


@sio.on('OnEvents')
def OnEvents(message):
    ''' 监听相关事件'''
    print(message)


# -----------------------------------------------------

def main():
    try:
        sio.connect(webapi, transports=['websocket'])
        # pdb.set_trace() 这是断点
        sio.wait()
    except BaseException as e:
        logging.info(e)
        print(e)


if __name__ == '__main__':
    # refreshkey()
    main()
