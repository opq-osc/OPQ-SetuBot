import asyncio
import aiohttp
from sex_pic import *



async def send_text(toid, type, msg, groupid, atuser=''):
    params = {'qq': robotqq,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": type,
            "sendMsgType": "TextMsg",
            "content": msg,
            "groupid": groupid,
            "atUser": atuser}
    async with aiohttp.ClientSession() as session:
        while 1:
            async with session.post(url=api, params=params, json=data, timeout=15) as res:
                result = await res.json()
                print('文字消息返回', result['Ret'])
                await asyncio.sleep(1)
            if result['Ret'] == 0:
                return
                # break
            else:
                await asyncio.sleep(1)
        # return

async def send_pic(toid, type, msg, groupid, atuser, picurl='', picbase64='', picmd5=''):
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
    async with aiohttp.ClientSession() as session:
        while 1:
            async with session.post(url=api, params=params, json=data, timeout=20) as res:
                result = await res.json()
                print('图片消息返回', result['Ret'])
            if result['Ret'] == 0:
                break
            else:
                await asyncio.sleep(1)
        # return


async def friend_send_text(data, msg):
    if data.FromQQG == 0:  # 好友
        await send_text(data.ToQQ, 1, msg, data.FromQQG, 0)
        return
    else:  # 临时
        await send_text(data.ToQQ, 3, msg, data.FromQQG, 0)
        return


async def friend_send_pic(data, msg, url, base64code):
    if data.FromQQG == 0:  # 临时会话
        await send_pic(data.ToQQ, 1, msg, 0, 0, url, base64code)
        return
    else:  # 好友
        await send_pic(data.ToQQ, 3, msg, data.FromQQG, 0, url, base64code)
        return

async def send_pic_callback(fut, callback):
    result = await fut
    await callback(data, msg, url, base64code,result)
    print('异步')
    return