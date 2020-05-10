import socketio
import requests
import re
import logging
import time
import base64
import json
import psutil
import cpuinfo
import datetime

with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
    print('获取配置成功~')

# globals().update(config)  # 神奇的方法,但是这样IDE总是提示没有变量
# setu_pattern = re.compile(setu_pattern)
# setunum_pattern = re.compile(setunum_pattern)

color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
size1200 = config['size1200']  # 是否使用 master_1200 缩略图，即长或宽最大为1200px的缩略图，以节省流量或提升加载速度（某些原图的大小可以达到十几MB）
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
robotqq = config['robotqq']  # 机器人QQ号
setu_pattern = re.compile(config['setu_pattern'])  # 色图正则
setunum_pattern = re.compile(config['setunum_pattern'])  # 色图正则1
path = config['path']  # 色图路径
# -----------------------------------------------------
api = webapi + '/v1/LuaApiCaller'
sio = socketio.Client()
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


def get_cpu_info():
    info = cpuinfo.get_cpu_info()  # 获取CPU型号等
    cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
    xc_count = psutil.cpu_count()  # 线程数，如双核四线程
    cpu_percent = round((psutil.cpu_percent()), 2)  # cpu使用率
    try:
        model = info['brand']
    except:
        model = info['hardware']
    try:
        freq = info['hz_actual']
    except:
        freq = 'null'
    cpu_info = (model, freq, info['arch'], cpu_count, xc_count, cpu_percent)
    return cpu_info


def get_memory_info():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 3)  # 总内存
    used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 3)  # 已用内存
    free_nc = round((float(memory.free) / 1024 / 1024 / 1024), 3)  # 空闲内存
    percent_nc = memory.percent  # 内存使用率
    swap_total = round((float(swap.total) / 1024 / 1024 / 1024), 3)  # 总swap
    swap_used = round((float(swap.used) / 1024 / 1024 / 1024), 3)  # 已用swap
    swap_free = round((float(swap.free) / 1024 / 1024 / 1024), 3)  # 空闲swap
    swap_percent = swap.percent  # swap使用率
    men_info = (total_nc, used_nc, free_nc, percent_nc, swap_total, swap_used, swap_free, swap_percent)
    return men_info


def uptime():
    now = time.time()
    boot = psutil.boot_time()
    boottime = datetime.datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
    nowtime = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
    up_time = str(datetime.datetime.utcfromtimestamp(now).replace(microsecond=0) - datetime.datetime.utcfromtimestamp(
        boot).replace(microsecond=0))
    alltime = (boottime, nowtime, up_time)
    return alltime


def sysinfo():
    cpu_info = get_cpu_info()
    mem_info = get_memory_info()
    up_time = uptime()
    msg = 'CPU型号:{0}\r\n频率:{1}\r\n架构:{2}\r\n核心数:{3}\r\n线程数:{4}\r\n负载:{5}%\r\n{6}\r\n' \
          '总内存:{7}G\r\n已用内存:{8}G\r\n空闲内存:{9}G\r\n内存使用率:{10}%\r\n{6}\r\n' \
          'swap:{11}G\r\n已用swap:{12}G\r\n空闲swap:{13}G\r\nswap使用率:{14}%\r\n{6}\r\n' \
          '开机时间:{15}\r\n当前时间:{16}\r\n已运行时间:{17}'
    full_meg = msg.format(cpu_info[0], cpu_info[1], cpu_info[2], cpu_info[3], cpu_info[4], cpu_info[5], '*' * 20,
                          mem_info[0], mem_info[1], mem_info[2], mem_info[3], mem_info[4],
                          mem_info[5], mem_info[6], mem_info[7], up_time[0], up_time[1], up_time[2])
    return full_meg


def base_64(filename):
    with open(path + filename, 'rb') as f:
        coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        print('本地base64转码~')
        return coding.decode()


def setuapi_1(tag='', r18=False):
    url = 'http://api.yuban10703.xyz:2333/setu'
    params = {'r18': r18,
              'tag': tag}
    try:
        res = requests.get(url, params, timeout=5)
    except:
        return '', '', '请求出错啦~'
    setu_data = res.json()
    # print(res.status_code)
    if res.status_code == 200:
        if setu_data['_id'] not in sent:
            sent.append(setu_data['_id'])
            title = setu_data['title']
            author = setu_data['author']
            artworkid = setu_data['artwork']
            artistid = setu_data['artist']
            filename = setu_data['filename'][0]
            if path == '':
                url = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename
                base64_code = ''
            else:
                url = ''
                base64_code = base_64(filename)
            msg = pixiv_url(title, artworkid, author, artistid)
            return url, base64_code, msg
    return '', '', 'error'


def setuapi_0(keyword='', r18=False):
    url = 'https://api.lolicon.app/setu/'
    params = {'r18': r18,
              'apikey': color_pickey,
              'keyword': keyword,
              'size1200': size1200,
              'proxy': 'i.pixiv.cat'}
    try:
        setu_data = requests.get(url, params, timeout=5).json()
    except:
        return '', '服务器爆炸啦~'
    if setu_data['code'] == 404:
        return '', '你的xp好奇怪啊 爪巴'
    if setu_data['code'] == 429:
        return '', '没图了 爪巴'
    picurl = setu_data['data'][0]['url']  # 提取图片链接
    author = setu_data['data'][0]['author']  # 提取作者名字
    title = setu_data['data'][0]['title']  # 图片标题
    artworkid = setu_data['data'][0]['pid']
    artistid = setu_data['data'][0]['uid']
    msg = pixiv_url(title, artworkid, author, artistid)
    return picurl, msg


def pixiv_url(title, artworkid, author, artistid):  # 拼凑消息
    purl = "www.pixiv.net/artworks/" + str(artworkid)  # 拼凑p站链接
    uurl = "www.pixiv.net/users/" + str(artistid)  # 画师的p站链接
    msg = title + "\r\n" + purl + "\r\n" + author + "\r\n" + uurl
    return msg


def send_text(toid, type, msg, groupid, atuser):
    params = {'qq': robotqq,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": type,
            "sendMsgType": "TextMsg",
            "content": msg,
            "groupid": groupid,
            "atUser": atuser}
    res = requests.post(api, params=params, json=data, timeout=3)
    print('文字消息:', res.json())
    return
    # print('已发送~')


def friend_send_text(data, msg):
    if data.FromQQG == 0:  # 好友
        send_text(data.ToQQ, 1, msg, data.FromQQG, 0)
        return
    else:  # 临时
        send_text(data.ToQQ, 3, msg, data.FromQQG, 0)
        return


def friend_send_pic(data, msg, url, base64code):
    if data.FromQQG == 0:  # 临时会话
        send_pic(data.ToQQ, 1, msg, 0, 0, url, base64code)
        return
    else:  # 好友
        send_pic(data.ToQQ, 3, msg, data.FromQQG, 0, url, base64code)
        return


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
    req = requests.post(api, params=params, json=data, timeout=30)
    print('图片消息:', req.json())


sent = []


def nmsl():
    api = 'https://nmsl.shadiao.app/api.php?from=sunbelife'
    res = requests.get(url=api).text
    return res


def get_setu(keyword, r18=False):
    data = setuapi_1(keyword, r18)
    # print(data[2])
    if data[0] != data[1]:
        # sent.append(data['_id'])
        print('尝试从yubanのapi获取')
        return data[0], data[1], data[2]
    else:
        print('尝试从lolicon获取')
        data_1 = setuapi_0(keyword, r18)
        if data_1[0] != '':
            return data_1[0], '', data_1[1]
        else:
            return '', '', data_1[1]


def beat():
    global sent
    while True:
        # sio.emit('GetWebConn', robotqq)
        print('sent:', sent)
        sent = []
        time.sleep(600)


@sio.event
def connect():
    sio.emit('GetWebConn', robotqq)  # 取得当前已经登录的QQ链接
    print('连接成功~')
    beat()  # 心跳包，保持对服务器的连接


@sio.on('OnGroupMsgs')
def OnGroupMsgs(message):
    ''' 监听群组消息'''
    tmp = message['CurrentPacket']['Data']
    a = GMess(tmp)
    # print(tmp)
    '''
    a.FrQQ 消息来源
    a.QQGName 来源QQ群昵称
    a.FromQQG 来源QQ群
    a.FromNickName 来源QQ昵称
    a.Content 消息内容
    '''
    # print(a.QQGName, '———', a.FromQQName, ':', a.Content)
    setu_keyword = setu_pattern.match(a.Content)
    # num_keyword = setunum_pattern.match(a.Content)
    if setu_keyword:
        keyword = setu_keyword.group(1)
        send_text(a.FromQQG, 2, '', 0, a.FromQQ)
        setu = get_setu(keyword)
        if setu[0] == setu[1]:
            send_text(a.FromQQG, 2, setu[2], 0, 0)
            return
        send_pic(a.FromQQG, 2, setu[2], a.FromQQ, a.FromQQ, setu[0], setu[1])
        # print('发送成功~')
        # time.sleep(5)
        return

    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        send_text(a.FromQQG, 2, msg, 0, 0)
        return
    # -----------------------------------------------------
    # print('@消息:',a.Atmsg)
    if 'nmsl' in a.Atmsg:
        msg = nmsl()
        send_text(a.FromQQG, 2, '\r\n' + msg, 0, a.FromQQ)
        return


@sio.on('OnFriendMsgs')
def OnFriendMsgs(message):
    ''' 监听好友消息 '''
    tmp = message['CurrentPacket']['Data']
    a = Mess(tmp)
    # print(tmp)
    # print('好友:', a.Content)
    keyword = setu_pattern.match(a.Content)
    if keyword:
        keyword = keyword.group(1)
        friend_send_text(a, '发送ing')
        setu = get_setu(keyword, r18=True)
        if setu[0] == setu[1]:
            friend_send_text(a, setu[2])
            return
        friend_send_pic(a, setu[2], setu[0], setu[1])
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        friend_send_text(a, msg)
        return
    # -----------------------------------------------------
    if a.Content == 'nmsl':
        msg = nmsl()
        friend_send_text(a, msg)
        return


@sio.on('OnEvents')
def OnEvents(message):
    ''' 监听相关事件'''
    # print(message)


# -----------------------------------------------------

def main():
    try:
        sio.connect(webapi, transports=['websocket'])
        # pdb.set_trace() 这是断点
        sio.wait()
    except BaseException as e:
        logging.info(e)
        # print(e)


if __name__ == '__main__':
    main()
