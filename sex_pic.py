import socketio, requests, re, time, base64, random, json, psutil, cpuinfo, datetime, threading
from queue import Queue

with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
    print('获取配置成功~')
color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
botqqs = config['botqqs']  # 机器人QQ号
setu_pattern = re.compile(config['setu_pattern'])  # 色图正则
setu_path = config['path']  # 色图路径
send_pic_original = config['send_pic_original']  # 是否发送原图
setu_threshold = config['setu_threshold']  # 发送上限
threshold_to_send = config['threshold_to_send']  # 超过上限后发送的文字
notfound_to_send = config['notfound_to_send']  # 没找到色图返回的文字
wrong_input_to_send = config['wrong_input_to_send']  # 关键字错误返回的文字
before_nmsl_to_send = config['before_nmsl_to_send']  # 嘴臭之前发送的语句
before_setu_to_send = config['before_setu_to_send']  # 发色图之前的语句
blacklist = config['blacklist']
whitelist = config['whitelist']
r18_whitelist = config['r18_whitelist']
r18_only_whitelist = config['r18_only_whitelist']
# -----------------------------------------------------
sio = socketio.Client()
q = Queue(maxsize=0)
# -----------------------------------------------------
api = webapi + '/v1/LuaApiCaller'


# -----------------------------------------------------


class GMess:
    # 群消息
    def __init__(self, message):
        self.messtype = 'group'  # 标记群聊
        self.CurrentQQ = message['CurrentQQ']  # 接收到这条消息的QQ
        self.FromQQG = message['CurrentPacket']['Data']['FromGroupId']  # 来源QQ群
        self.QQGName = message['CurrentPacket']['Data']['FromGroupName']  # 来源QQ群昵称
        self.FromQQ = message['CurrentPacket']['Data']['FromUserId']  # 哪个QQ发过来的
        self.FromQQName = message['CurrentPacket']['Data']['FromNickName']  # 来源QQ名称(群内)
        if message['CurrentPacket']['Data']['MsgType'] == 'TextMsg':  # 普通消息
            self.Content = message['CurrentPacket']['Data']['Content']  # 消息内容
            self.At_Content = ''
        elif message['CurrentPacket']['Data']['MsgType'] == 'AtMsg':  # at消息
            self.At_Content = re.sub(r'@.* ', '',
                                     json.loads(message['CurrentPacket']['Data']['Content'])['Content'])  # AT消息内容
            self.Content = ''  # 消息内容
        else:
            self.At_Content = ''
            self.Content = ''  # 消息内容


class Mess:
    # 私聊消息
    def __init__(self, message):
        # print(message)
        self.messtype = 'private'  # 标记私聊
        self.CurrentQQ = message['CurrentQQ']  # 接收到这条消息的QQ
        self.QQ = message['CurrentPacket']['Data']['ToUin']  # 接收到这条消息的QQ
        self.FromQQ = message['CurrentPacket']['Data']['FromUin']  # 哪个QQ发过来的
        if message['CurrentPacket']['Data']['MsgType'] == 'TextMsg':  # 普通消息
            self.Content = message['CurrentPacket']['Data']['Content']  # 消息内容
            self.FromQQG = 0
        elif message['CurrentPacket']['Data']['MsgType'] == 'TempSessionMsg':  # 临时消息
            self.FromQQG = message['CurrentPacket']['Data']['TempUin']  # 通过哪个QQ群发起的
            self.Content = json.loads(message['CurrentPacket']['Data']['Content'])['Content']
        else:
            self.Content = ''
            self.FromQQG = 0


def send_text(mess, msg, atuser=0):
    if mess.messtype == 'group':
        t = 2  # 群聊
        toid = mess.FromQQG
    else:
        toid = mess.FromQQ  # 来自谁
        if mess.FromQQG == 0:  # 0为好友会话
            t = 1
        else:
            t = 3  # 3为临时会话
    params = {'qq': mess.CurrentQQ,  # bot的qq
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": t,
            "sendMsgType": "TextMsg",
            "content": msg,
            "groupid": mess.FromQQG,
            "atUser": atuser}
    res = requests.post(api, params=params, json=data, timeout=None)
    try:
        ret = res.json()['Ret']
    except:
        ret = '返回错误~'
    print('文字消息发送状态:{0} Ret:{1}'.format(res.status_code, ret))
    return


def send_pic(mess, msg, atuser=0, picurl='', picbase64='', picmd5=''):
    if mess.messtype == 'group':
        t = 2  # 群聊
        toid = mess.FromQQG
    else:
        toid = mess.FromQQ  # 来自谁
        if mess.FromQQG == 0:  # FromQQG为0是好友会话
            t = 1
        else:
            t = 3  # 3为临时会话
    params = {'qq': mess.CurrentQQ,
              'funcname': 'SendMsg'}
    data = {"toUser": toid,
            "sendToType": t,
            "sendMsgType": "PicMsg",
            "content": msg,
            "groupid": mess.FromQQG,
            "atUser": atuser,
            "picUrl": picurl,
            "picBase64Buf": picbase64,
            "fileMd5": picmd5}
    res = requests.post(api, params=params, json=data, timeout=None)
    try:
        ret = res.json()['Ret']
    except:
        ret = '返回错误~'
    print('图片消息发送状态:{0} Ret:{1}'.format(res.status_code, ret))
    return


def get_cpu_info():
    info = cpuinfo.get_cpu_info()  # 获取CPU型号等
    cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
    xc_count = psutil.cpu_count()  # 线程数，如双核四线程
    cpu_percent = round((psutil.cpu_percent()), 2)  # cpu使用率
    model = info['brand_raw']  # cpu型号
    try:  # 频率
        freq = info['hz_actual_friendly']
    except:
        freq = 'null'
    cpu_info = (model, freq, info['arch_string_raw'], cpu_count, xc_count, cpu_percent)
    return cpu_info


def get_memory_info():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 3)  # 总内存
    used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 3)  # 已用内存
    available_nc = round((float(memory.available) / 1024 / 1024 / 1024), 3)  # 空闲内存
    percent_nc = memory.percent  # 内存使用率
    swap_total = round((float(swap.total) / 1024 / 1024 / 1024), 3)  # 总swap
    swap_used = round((float(swap.used) / 1024 / 1024 / 1024), 3)  # 已用swap
    swap_free = round((float(swap.free) / 1024 / 1024 / 1024), 3)  # 空闲swap
    swap_percent = swap.percent  # swap使用率
    men_info = (total_nc, used_nc, available_nc, percent_nc, swap_total, swap_used, swap_free, swap_percent)
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


def nmsl():
    api = 'https://nmsl.shadiao.app/api.php?from=sunbelife'
    res = requests.get(url=api).text
    return res


class Setu:
    def __init__(self, msg_in, tag='', num=1, r18=0):
        self.msg_in = msg_in
        self.tag = tag
        self.num = num  # 尝试获取的数量
        self.num_real = 0  # 实际的数量
        self.api_1_num = 0  # api1
        self.r18 = r18
        self.setudata = None
        self.msg = []  # 待发送的消息
        self.download_url = []
        self.base64_codes = []

    def build_msg(self, title, artworkid, author, artistid, page, url_original):
        purl = "www.pixiv.net/artworks/" + str(artworkid)  # 拼凑p站链接
        uurl = "www.pixiv.net/users/" + str(artistid)  # 画师的p站链接
        page = 'p' + str(page)
        msg = ('标题:{title}\r\n{purl}\r\npage:{page}\r\n作者:{author}\r\n{uurl}\r\n原图:{url_original}'.format(
            title=title, purl=purl, page=page, author=author,
            uurl=uurl, url_original=url_original))
        return msg

    def base_64(self, filename):
        with open(filename, 'rb') as f:
            coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            print('本地base64转码~')
            return coding.decode()

    def api_0(self):
        print('尝试从yubanのapi获取')
        url = 'http://api.yuban10703.xyz:2333/setu_v3'
        params = {'type': self.r18,
                  'num': self.num,
                  'tag': self.tag}
        try:
            res = requests.get(url, params, timeout=5)
            setu_data = res.json()
            status_code = res.status_code
            assert status_code == 200
            print('获取到{0}张setu'.format(setu_data['count']))  # 打印获取到多少条
            self.num_real = setu_data['count']  # 实际获取到多少条
            for data in setu_data['data']:
                filename = data['filename']
                url_original = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/' + filename
                msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'], data['page'],
                                     url_original)
                self.msg.append(msg)
                if setu_path == '':  # 非本地
                    self.base64_codes.append('')
                    if send_pic_original:  # 发送原画
                        self.download_url.append(url_original)
                    else:
                        self.download_url.append('https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename)
                else:  # 本地
                    self.base64_codes.append(self.base_64(setu_path + filename))
                    self.download_url.append('')
                    # self.download_url.append(data[send_pic_type])
        except:
            pass

    def api_1(self):
        if self.r18 == 1:
            r18 = 0
        elif self.r18 == 3:
            r18 = 2
        elif self.r18 == 2:
            r18 = 1
        else:
            r18 = 0
        print('尝试从lolicon获取')
        url = 'https://api.lolicon.app/setu/'
        params = {'r18': r18,
                  'apikey': color_pickey,
                  'keyword': self.tag,
                  'num': self.api_1_num,
                  'size1200': not send_pic_original,
                  'proxy': 'disable'}
        try:
            res = requests.get(url, params, timeout=5)
            setu_data = res.json()
            status_code = res.status_code
            assert status_code == 200
            self.num_real = setu_data['count']  # 实际获取到多少条
            print('获取到{0}张setu'.format(setu_data['count']))  # 打印获取到多少条
            for data in setu_data['data']:
                msg = self.build_msg(data['title'], data['pid'], data['author'], data['uid'], data['p'], '无~')
                self.msg.append(msg)
                self.download_url.append(data['url'])
                self.base64_codes.append('')
        except:
            pass

    def main(self):
        self.api_0()
        if self.num_real < self.num:  # 如果实际数量小于尝试获取的数量
            self.api_1_num = self.num - self.num_real
            self.api_1()
            if self.num_real == 0:
                send_text(self.msg_in, notfound_to_send, 0)
        for i in range(len(self.msg)):
            print('进入队列')
            q.put({'mess': self.msg_in, 'msg': self.msg[i], 'download_url': self.download_url[i],
                   'base64code': self.base64_codes[i]})


def send_setu(mess, num, tag, r18):
    if num != '':  # 如果指定了色图数量
        try:  # 将str转换成int
            num = int(num)
            if num > int(setu_threshold):  # 如果指定数量超过设定值就返回指定消息
                send_text(mess, threshold_to_send)
                return
            if num <= 0:
                send_text(mess, '¿')
                return
        except:  # 如果失败了就说明不是整数数字
            send_text(mess, wrong_input_to_send)
            return
    else:  # 没指定的话默认是1
        num = 1
    setu = Setu(mess, tag, num, r18)
    setu.main()


@sio.event
def connect():
    for botqq in botqqs:
        sio.emit('GetWebConn', str(botqq))  # 取得当前已经登录的QQ链接
    while True:
        data = q.get()
        t = threading.Thread(target=send_pic,
                             args=(data['mess'], data['msg'], 0, data['download_url'], data['base64code']))
        t.start()
        q.task_done()
        time.sleep(1.1)


@sio.event
def OnGroupMsgs(message):
    a = GMess(message)
    setu_keyword = setu_pattern.match(a.Content)
    if setu_keyword:
        if blacklist != [] and whitelist != []:  # 如果黑白名单中有数据
            if a.FromQQG in blacklist:  # 如果在黑名单直接返回
                return
            if a.FromQQG not in whitelist and whitelist != []:  # 如果不在白名单里,且白名单不为空,直接返回
                return
        if a.FromQQG in r18_whitelist:  # 如果在r18列表中,返回混合内容
            r18 = 3
            if a.FromQQG in r18_only_whitelist:  # 如果在r18only中,返回porn的内容
                r18 = 2
        else:
            r18 = random.choice([0, 1])  # 从普通和性感中二选一
        num = setu_keyword.group(1)  # 提取数量
        tag = setu_keyword.group(2)  # 提取tag
        send_setu(a, num, tag, r18)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        send_text(a, msg)
        return
    # -----------------------------------------------------
    if a.At_Content == 'nmsl':
        msg = nmsl()
        send_text(a, msg)
        return


@sio.event
def OnFriendMsgs(message):
    a = Mess(message)
    setu_keyword = setu_pattern.match(a.Content)
    if setu_keyword:
        if blacklist != [] and whitelist != []:  # 如果黑白名单中有数据
            if a.FromQQG in blacklist:
                return
            if a.FromQQG not in whitelist and whitelist != []:
                return
        num = setu_keyword.group(1)  # 提取数量
        tag = setu_keyword.group(2)  # 提取tag
        send_setu(a, num, tag, 2)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        send_text(a, msg)
        return
    # -----------------------------------------------------
    if a.Content == 'nmsl':
        msg = nmsl()
        send_text(a, msg)
        return


@sio.event
def OnEvents(message):
    ''' 监听相关事件'''
    # print(message)


if __name__ == '__main__':
    try:
        sio.connect(webapi, transports=['websocket'])
        sio.wait()
    except BaseException as e:
        print(e)
