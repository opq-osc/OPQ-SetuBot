from api import *
import socketio
import asyncio
import aiohttp
import re
import threading
import time

sio = socketio.AsyncClient()
api = 'http://10.1.1.169:8888'
robotqq = ''  # 机器人QQ号
sexpic_key = ''  # 申请地址api.lolicon.app
size1200 = 'true'  # 是否使用 master_1200 缩略图，即长或宽最大为1200px的缩略图，以节省流量或提升加载速度（某些原图的大小可以达到十几MB）


class GMess:
    # QQ群消息类型
    def __init__(self, message):
        # print(message)
        self.FromQQG = message['FromGroupId']  # 来源QQ群
        self.QQGName = message['FromGroupName']  # 来源QQ群昵称
        self.FromQQ = message['FromUserId']  # 来源QQ
        self.FromQQName = message['FromNickName']  # 来源QQ名称
        self.Content = message['Content']  # 消息内容


class FMess:
    def __init__(self, message):
        self.FromQQ = message['ToUin']
        self.ToQQ = message['FromUin']
        self.Content = message['Content']
        try:
            self.FromQQG = message['TempUin']
        except:
            self.FromQQG = 0


# 定义一个专门创建事件循环loop的函数，在另一个线程中启动它
def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


@sio.event
async def connect():
    print("连接成功")
    t.start()
    while True:
        await sio.emit('GetWebConn', robotqq)
        await asyncio.sleep(30)


@sio.event
async def OnGroupMsgs(data):
    mess = GMess(data['CurrentPacket']['Data'])
    keyword = re.match(r'来[点丶张](.*?)的{0,1}色图', mess.Content)  # 瞎写的正则
    if keyword:
        asyncio.run_coroutine_threadsafe(send_text(mess.FromQQG, 2, '尝试发送ing~~', 0, mess.FromQQ), new_loop)
        future = asyncio.run_coroutine_threadsafe(sex_pic(0, keyword.group(1)), new_loop)
        asyncio.run_coroutine_threadsafe(
            send_pic(mess.FromQQG, 2, future.result()[0], 0, mess.FromQQ, future.result()[1]), new_loop)


@sio.event
async def OnFriendMsgs(data):
    mess = FMess(data['CurrentPacket']['Data'])
    # print(mess.Content)
    keyword = re.match(r'来[点丶张](.*?)的{0,1}色图', mess.Content)  # 瞎写的正则
    if keyword:
        asyncio.run_coroutine_threadsafe(send_text(mess.ToQQ, 3, '发送ing~~', mess.FromQQG, 0), new_loop)
        future = asyncio.run_coroutine_threadsafe(sex_pic(1, keyword.group(1)), new_loop)
        asyncio.run_coroutine_threadsafe(
            send_pic(mess.ToQQ, 3, future.result()[0], mess.FromQQG, 0, future.result()[1]), new_loop)


async def main():
    await sio.connect(api, transports=['websocket'])
    print('client connected id:', sio.sid)
    # await sio.disconnect()
    await sio.wait()
    await sio.disconnect()


if __name__ == '__main__':
    new_loop = asyncio.new_event_loop()  # 在当前线程下创建时间循环，（未启用），在start_loop里面启动它
    t = threading.Thread(target=start_loop, args=(new_loop,))  # 通过当前线程开启新的线程去启动事件循环
    asyncio.run(main())
