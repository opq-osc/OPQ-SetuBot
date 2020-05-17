from bot_apis import *
from function_apis import *
import socketio
import requests
import re
import logging
import time
import json
import psutil
import cpuinfo
import datetime
import asyncio

with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
    print('获取配置成功~')
sent = []  # 记录发送过的id
color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
size1200 = config['size1200']  # 是否使用 master_1200 缩略图，即长或宽最大为1200px的缩略图，以节省流量或提升加载速度（某些原图的大小可以达到十几MB）
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
robotqq = config['robotqq']  # 机器人QQ号
setu_pattern = re.compile(config['setu_pattern'])  # 色图正则
setunum_pattern = re.compile(config['setunum_pattern'])  # 色图正则1
path = config['path']  # 色图路径
# -----------------------------------------------------
api = webapi + '/v1/LuaApiCaller'
sio = socketio.AsyncClient()

# log文件处理
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=0,
                    filename='new.log', filemode='a')


class GMess:
    # QQ群消息类型
    def __init__(self, message):
        self.FromQQG = message['FromGroupId']  # 来源QQ群
        self.QQGName = message['FromGroupName']  # 来源QQ群昵称
        self.FromQQ = message['FromUserId']  # 来源QQ
        self.FromQQName = message['FromNickName']  # 来源QQ名称
        self.Content = message['Content']  # 消息内容
        try:
            if robotqq == str(json.loads(message['Content'])['UserID'][0]):
                self.Atmsg = json.loads(message['Content'])['Content']
            else:
                self.Atmsg = ''
        except:
            self.Atmsg = ''
        # except:
        #     print('?????')
        # if robotqq in json.loads(message['Content'])['UserID']:
        #     print('>>>aaaa<<<')
        #     self.Atmsg = json.loads(message['Content'])['Content']


class Mess:
    def __init__(self, message):
        # print(message)
        self.FromQQ = message['ToUin']
        self.ToQQ = message['FromUin']
        try:
            self.Content = json.loads(message['Content'])['Content']
        except:
            self.Content = message['Content']
        try:
            self.FromQQG = message['TempUin']
        except:
            self.FromQQG = 0


# def beat():
#     while True:
#         sio.emit('GetWebConn', robotqq)
#         print('sent:', sent)
#         sent.clear()
#         time.sleep(600)


@sio.event
async def connect():
    await sio.emit('GetWebConn', robotqq)  # 取得当前已经登录的QQ链接
    print('连接成功~')
    beat()  # 心跳包，保持对服务器的连接


@sio.event
async def OnGroupMsgs(message):
    ''' 监听群组消息'''
    a = GMess(message['CurrentPacket']['Data'])
    '''
    a.FrQQ 消息来源
    a.QQGName 来源QQ群昵称
    a.FromQQG 来源QQ群
    a.FromNickName 来源QQ昵称
    a.Content 消息内容
    '''
    # print(a.QQGName, '&', a.FromQQName, ':', a.Content)
    setu_keyword = setu_pattern.match(a.Content)
    # num_keyword = setunum_pattern.match(a.Content)
    if a.Content == 'test':
        sendtext = asyncio.create_task(send_text(a.FromQQG, 2, '', 0, a.FromQQ))
        getsetu = asyncio.create_task(get_setu(''))
        print(getsetu.result()[2])
        await asyncio.gather(sendtext,getsetu)
        if getsetu.result()[0] == getsetu.result()[1]:
            await send_text(a.FromQQG, 2, getsetu.result()[2], 0, 0)
            return
        print('???')
        sendpic = asyncio.create_task(send_pic(a.FromQQG, 2, getsetu.result()[2], a.FromQQ, a.FromQQ, getsetu.result()[0], getsetu.result()[1]))
        await sendpic
        return
        # return
        # print('????????????')
        # if setu[0] == setu[1]:
        #     send_text(a.FromQQG, 2, setu[2], 0, 0)
        #     return

        # print('发送成功~')
        # time.sleep(5)


    # # -----------------------------------------------------
    # if a.Content == 'sysinfo':
    #     info = Sysinfo()
    #     msg = info.get_sysinfo()
    #     send_text(a.FromQQG, 2, msg, 0, 0)
    #     return
    # # -----------------------------------------------------
    # if 'nmsl' in a.Atmsg:
    #     print('@消息:', a.Atmsg)
    #     msg = nmsl()
    #     send_text(a.FromQQG, 2, '\r\n' + msg, 0, a.FromQQ)
    #     return

#
# @sio.event
# def OnFriendMsgs(message):
#     ''' 监听好友消息 '''
#     tmp = message['CurrentPacket']['Data']
#     a = Mess(tmp)
#     print(tmp)
#     print('好友:', a.Content)
#     keyword = setu_pattern.match(a.Content)
#     if keyword:
#         keyword = keyword.group(1)
#         friend_send_text(a, '发送ing')
#         setu = get_setu(keyword, r18=True)
#         if setu[0] == setu[1]:
#             friend_send_text(a, setu[2])
#             return
#         friend_send_pic(a, setu[2], setu[0], setu[1])
#         return
#     # -----------------------------------------------------
#     if a.Content == 'sysinfo':
#         info = Sysinfo()
#         msg = info.get_sysinfo()
#         friend_send_text(a, msg)
#         return
#     # -----------------------------------------------------
#     if a.Content == 'nmsl':
#         msg = nmsl()
#         friend_send_text(a, msg)
#         return

#
# @sio.on('OnEvents')
# def OnEvents(message):
#     ''' 监听相关事件'''
#     # print(message)


# -----------------------------------------------------

async def main():
    try:
        await sio.connect(webapi, transports=['websocket'])
        await sio.emit('GetWebConn', robotqq)  # 取得当前已经登录的QQ链接
        # pdb.set_trace() 这是断点
        await sio.wait()
    except BaseException as e:
        logging.info(e)
        # print(e)


if __name__ == '__main__':
    asyncio.run(main())
