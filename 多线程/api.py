import asyncio
import aiohttp
from sex_pic import *

Luaapi = api + '/v1/LuaApiCaller'


async def send_text(toid, type, msg, groupid, atuser=''):
    print('发送ing')
    params = {'qq': robotqq,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": type,
            "sendMsgType": "TextMsg",
            "content": msg,
            "groupid": groupid,
            "atUser": atuser}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=Luaapi, params=params, json=data, timeout=30) as res:
            print(await res.json())
            return 123, 456


async def send_pic(toid, type, msg='', groupid=0, atuser=0, picurl='', picbase64='', picmd5=''):
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
        async with session.post(Luaapi, params=params, json=data) as res:
            print(res.status)


async def sex_pic(r18, keyword=''):
    url = 'https://api.lolicon.app/setu/'
    params = {'r18': r18,
              'apikey': sexpic_key,
              'keyword': keyword,
              'size1200': size1200,
              'proxy': 'i.pixiv.cat'}
    errpicurl = 'https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/error.jpg'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, ) as res:
            try:
                data = await res.json()  # 转换成字典
                if data['code'] == 404:
                    return '你的xp好奇怪啊 爪巴', errpicurl
                elif data['code'] == 429:
                    return '今天的色图发完了 爪巴', errpicurl
                picurl = data['data'][0]['url']  # 提取图片链接
                author = data['data'][0]['author']  # 提取作者名字
                title = data['data'][0]['title']  # 图片标题
                purl = 'www.pixiv.net/artworks/' + str(data['data'][0]['pid'])  # 拼凑p站链接
                uurl = 'www.pixiv.net/users/' + str(data['data'][0]['uid'])  # 画师的p站链接
                msg = title + '\r\n' + purl + '\r\n' + author + '\r\n' + uurl  # 组合消息
                return msg, picurl
            except Exception:
                return '色图服务器可能挂掉了', errpicurl  # 出错了就返回固定值.....

# async def send_sexpic():
#     data = await sex_pic()
