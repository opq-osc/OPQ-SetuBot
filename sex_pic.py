from datetime import datetime

import socketio, requests, re, time, base64, random, json, psutil, cpuinfo, datetime, threading, sys
from queue import Queue, LifoQueue

with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
botqqs = config['botqqs']  # 机器人QQ号
setu_pattern = re.compile(config['setu_pattern'])  # 色图正则
setu_path = config['path']  # 色图路径
send_original_pic = config['send_original_pic']  # 是否发送原图
not_send_pic_info = config['not_send_pic_info']  # 是否只发图
setu_threshold = int(config['setu_threshold'])  # 发送上限
threshold_to_send = config['threshold_to_send']  # 超过上限后发送的文字
notfound_to_send = config['notfound_to_send']  # 没找到色图返回的文字
frequency_cap_to_send = config['frequency_cap_to_send']  # 达到频率上限后发送语句
wrong_input_to_send = config['wrong_input_to_send']  # 关键字错误返回的文字
before_nmsl_to_send = config['before_nmsl_to_send']  # 嘴臭之前发送的语句
before_setu_to_send_switch = config['before_setu_to_send_switch']  # 发色图之前是否发送消息
send_setu_at = config['send_setu_at']  # 发色图时是否@
before_setu_to_send = config['before_setu_to_send']  # 发色图之前的语句
group_blacklist = config['group_blacklist']
group_whitelist = config['group_whitelist']
group_r18_whitelist = config['group_r18_whitelist']
group_r18_only_whitelist = config['group_r18_only_whitelist']
private_for_group_blacklist = config['private_for_group_blacklist']
private_for_group_whitelist = config['private_for_group_whitelist']
private_for_group_r18_whitelist = config['private_for_group_r18_whitelist']
private_for_group_r18_only_whitelist = config['private_for_group_r18_only_whitelist']
private_r18 = config['private_r18']
group_r18_default = config['group_r18_default']
private_for_group_r18_default = config['private_for_group_r18_default']
RevokeMsg = config['RevokeMsg']
RevokeMsg_time = int(config['RevokeMsg_time'])
sentlist_switch = config['sentlist_switch']

frequency = config['frequency']
frequency_additional = config['frequency_additional']
reset_freq_time = config['reset_freq_time']

clear_sentlist_time = int(config['clear_sentlist_time'])
# -----------------------------------------------------
sio = socketio.Client()
q_pic = LifoQueue(maxsize=0)
q_text = LifoQueue(maxsize=0)
q_withdraw = Queue(maxsize=0)
# -----------------------------------------------------
api = webapi + '/v1/LuaApiCaller'
sent_list = []
freq_group_list = {}
time_tmp = time.time()
print('获取配置成功~')


# -----------------------------------------------------


class GMess:
    # 群消息
    def __init__(self, message):
        # print(message)
        self.messtype = 'group'  # 标记群聊
        self.CurrentQQ = message['CurrentQQ']  # 接收到这条消息的QQ
        self.FromQQG = message['CurrentPacket']['Data']['FromGroupId']  # 来源QQ群
        self.QQGName = message['CurrentPacket']['Data']['FromGroupName']  # 来源QQ群昵称
        self.FromQQ = message['CurrentPacket']['Data']['FromUserId']  # 哪个QQ发过来的
        self.FromQQName = message['CurrentPacket']['Data']['FromNickName']  # 来源QQ名称(群内)
        self.MsgSeq = message['CurrentPacket']['Data']['MsgSeq']
        self.MsgRandom = message['CurrentPacket']['Data']['MsgRandom']
        self.MsgType = message['CurrentPacket']['Data']['MsgType']
        if message['CurrentPacket']['Data']['MsgType'] == 'TextMsg':  # 普通消息
            self.Content = message['CurrentPacket']['Data']['Content']  # 消息内容
            self.At_Content = ''
        elif message['CurrentPacket']['Data']['MsgType'] == 'AtMsg':  # at消息
            self.At_Content = re.sub(r'.*@.* ', '',
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
    try:
        res = requests.post(api, params=params, json=data, timeout=3)
        ret = res.json()['Ret']
    except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
        ret = '超时~'
    except (ValueError, KeyError):
        ret = '返回错误~'
    except:
        ret = ("未知错误:", sys.exc_info()[0])
    print('文字消息执行状态:[Ret:{}]'.format(ret))
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
    try:
        res = requests.post(api, params=params, json=data, timeout=10)
        ret = res.json()['Ret']
    except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
        ret = '超时~'
    except (ValueError, KeyError):
        ret = '返回错误~'
    except BaseException as e:
        # ret = ("未知错误:", sys.exc_info()[0])
        ret = ("未知错误:", e)
    print('图片消息执行状态:[Ret:{}]'.format(ret))
    return


def withdraw_message(mess):
    params = {'qq': mess.FromQQ,
              'funcname': 'RevokeMsg'}
    data = {"GroupID": mess.FromQQG,
            "MsgSeq": mess.MsgSeq,
            "MsgRandom": mess.MsgRandom}
    time.sleep(RevokeMsg_time)
    try:
        res = requests.post(api, params=params, json=data, timeout=3)
        ret = res.json()['Ret']
    except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
        ret = '超时~'
    except (ValueError, KeyError):
        ret = '返回错误~'
    except:
        ret = ("未知错误:", sys.exc_info()[0])
    print('撤回消息执行状态:[Ret:{}]'.format(ret))
    return


def get_cpu_info():
    info = cpuinfo.get_cpu_info()  # 获取CPU型号等
    cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
    xc_count = psutil.cpu_count()  # 线程数，如双核四线程
    cpu_percent = round((psutil.cpu_percent()), 2)  # cpu使用率
    try:
        model = info['hardware_raw']  # cpu型号
    except:
        model = info['brand_raw']  # cpu型号
    try:  # 频率
        freq = info['hz_actual_friendly']
    except:
        freq = 'null'
    cpu_info = (model, freq, info['arch'], cpu_count, xc_count, cpu_percent)
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
        self.num_real_api_1 = 0  # api1的实际的数量
        self.api_1_num = 0  # api1
        self.r18 = r18
        self.setudata = None
        self.msg = []  # 待发送的消息
        self.download_url = []
        self.base64_codes = []

    def build_msg(self, title, artworkid, author, artistid, page, url_original):
        if not_send_pic_info:
            if send_setu_at and self.msg_in.messtype == 'group':
                msg = '[ATUSER({qq})]'.format(qq=self.msg_in.FromQQ)
            else:
                msg = ''
        else:
            purl = "www.pixiv.net/artworks/" + str(artworkid)  # 拼凑p站链接
            uurl = "www.pixiv.net/users/" + str(artistid)  # 画师的p站链接
            page = 'p' + str(page)
            if send_setu_at and self.msg_in.messtype == 'group':
                msg = '[ATUSER({qq})]\r\n标题:{title}\r\n{purl}\r\npage:{page}\r\n作者:{author}\r\n{uurl}\r\n原图:{url_original}'.format(
                    qq=self.msg_in.FromQQ, title=title, purl=purl, page=page, author=author,
                    uurl=uurl, url_original=url_original)
            else:
                msg = '标题:{title}\r\n{purl}\r\npage:{page}\r\n作者:{author}\r\n{uurl}\r\n原图:{url_original}'.format(
                    title=title, purl=purl, page=page, author=author,
                    uurl=uurl, url_original=url_original)
        return msg

    def base_64(self, filename):
        with open(filename, 'rb') as f:
            coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            print('本地base64转码~')
            return coding.decode()

    def api_0(self):
        url = 'http://api.yuban10703.xyz:2333/setu_v3'
        params = {'type': self.r18,
                  'num': self.num,
                  'tag': self.tag}
        try:
            res = requests.get(url, params, timeout=5)
            setu_data = res.json()
            status_code = res.status_code
            print('从yubanのapi获取到{0}张setu'.format(setu_data['count']))  # 打印获取到多少条
            if status_code == 200:
                self.num_real = setu_data['count']  # 实际获取到多少条
                for data in setu_data['data']:
                    filename = data['filename']
                    if filename in sent_list and sentlist_switch:  # 如果发送过
                        print('发送过~')
                        self.num_real -= 1
                        continue
                    url_original = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/' + filename
                    msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'], data['page'],
                                         url_original)
                    self.msg.append(msg)
                    if setu_path == '':  # 非本地
                        self.base64_codes.append('')
                        if send_original_pic:  # 发送原画
                            self.download_url.append(url_original)
                        else:
                            self.download_url.append('https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename)
                    else:  # 本地
                        self.base64_codes.append(self.base_64(setu_path + filename))
                        self.download_url.append('')
                        # self.download_url.append(data[send_pic_type])
                    sent_list.append(filename)  # 记录发送过的图
        except Exception as e:
            print(e)

    def api_1(self):
        # 兼容api
        if self.r18 == 1:
            r18 = 0
        elif self.r18 == 3:
            r18 = 2
        elif self.r18 == 2:
            r18 = 1
        else:
            r18 = 0
        url = 'https://api.lolicon.app/setu/'
        params = {'r18': r18,
                  'apikey': color_pickey,
                  'num': self.api_1_num,
                  'size1200': not send_original_pic,
                  'proxy': 'disable'}
        if (len(self.tag) != 0) and (not self.tag.isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            params['keyword'] = self.tag
        try:
            res = requests.get(url, params, timeout=5)
            setu_data = res.json()
            status_code = res.status_code
            assert status_code == 200
            self.num_real_api_1 = setu_data['count']  # 实际获取到多少条
            print('从lolicon获取到{0}张setu'.format(setu_data['count']))  # 打印获取到多少条
            for data in setu_data['data']:
                msg = self.build_msg(data['title'], data['pid'], data['author'], data['uid'], data['p'], '无~')
                self.msg.append(msg)
                self.download_url.append(data['url'])
                self.base64_codes.append('')
        except Exception as e:
            print(e)

    def main(self):
        self.api_0()
        if self.num_real < self.num:  # 如果实际数量小于尝试获取的数量
            self.api_1_num = self.num - self.num_real
            self.api_1()
            if self.num_real == 0 and self.num_real_api_1 == 0:  # 2个api都没获取到数据
                q_text.put({'mess': self.msg_in, 'msg': notfound_to_send, 'atuser': 0})
                # freq_group_list[self.msg_in.FromQQG] -= self.num
                return
        for i in range(len(self.msg)):
            # print('进入队列')
            q_pic.put({'mess': self.msg_in, 'msg': self.msg[i], 'download_url': self.download_url[i],
                       'base64code': self.base64_codes[i]})


def send_setu(mess, num, tag):
    # ------------------------------------------群聊黑白名单-------------------------------------------------------

    if mess.messtype == 'group':  # 群聊
        r18 = group_r18_default  # 默认
        if group_blacklist != [] and group_whitelist != []:  # 如果群黑白名单中有数据
            if mess.FromQQG in group_blacklist:  # 如果在黑名单直接返回
                return
            if mess.FromQQG not in group_whitelist and group_whitelist != []:  # 如果不在白名单里,且白名单不为空,直接返回
                return
        if mess.FromQQG in group_r18_whitelist:  # 如果在r18列表中,返回混合内容
            r18 = 3
            if mess.FromQQG in group_r18_only_whitelist:  # 如果在r18only中,返回porn的内容
                r18 = 2
    # ------------------------------------------临时会话黑白名单----------------------------------------------

    elif mess.messtype == 'private' and mess.FromQQG != 0:  # 临时会话
        r18 = private_for_group_r18_default  # 默认
        if private_for_group_blacklist != [] and private_for_group_whitelist != []:  # 是临时会话且黑白名单中有数据
            if mess.FromQQG in private_for_group_blacklist:  # 如果在黑名单直接返回
                return
            if mess.FromQQG not in private_for_group_whitelist and private_for_group_whitelist != []:  # 如果不在白名单里,且白名单不为空,直接返回
                return
        if mess.FromQQG in private_for_group_r18_whitelist:  # 如果在r18列表中,返回混合内容
            r18 = 3
            if mess.FromQQG in private_for_group_r18_only_whitelist:  # 如果在r18only中,返回porn的内容
                r18 = 2
    elif mess.FromQQG == 0 and private_r18:  # 好友会话
        r18 = private_r18
    else:  # 好像没什么用的else.....
        r18 = random.choices([0, 1], [1, 10], k=1)  # 从普通和性感中二选一

    # 阿巴阿巴阿巴阿巴阿巴阿巴--------------------num部分----------------------------------------------------
    if num != '':  # 如果指定了色图数量
        try:  # 将str转换成int
            num = int(num)
            if num > setu_threshold:  # 如果指定数量超过设定值就返回指定消息
                # send_text(mess, threshold_to_send)
                q_text.put({'mess': mess, 'msg': threshold_to_send, 'atuser': 0})
                return
            if num <= 0:
                q_text.put({'mess': mess, 'msg': '¿', 'atuser': 0})
                # send_text(mess, '¿')
                return
        except:  # 如果失败了就说明不是整数数字
            # send_text(mess, wrong_input_to_send)
            q_text.put({'mess': mess, 'msg': wrong_input_to_send, 'atuser': 0})
            return
    else:  # 没指定的话默认是1
        num = 1
    # -----------------------------频率控制--------------------------------------------------------
    try:
        if mess.messtype == 'group':  # 只控制群聊
            if str(mess.FromQQG) not in frequency_additional.keys() and frequency != 0:  # 非自定义频率的群且限制不为0
                if (num + int(freq_group_list[mess.FromQQG])) > int(frequency) or (num > frequency):  # 大于限制频率
                    q_text.put(
                        {'mess': mess,
                         'msg': frequency_cap_to_send.format(reset_freq_time=reset_freq_time, frequency=int(frequency),
                                                             num=int(freq_group_list[
                                                                         mess.FromQQG]), refresh_time=round(
                                 reset_freq_time - (time.time() - time_tmp))),
                         'atuser': 0})
                    return
                freq_group_list[mess.FromQQG] += num  # 计数
            else:
                if int(frequency_additional[str(mess.FromQQG)]):  # 如果自定义频率不为0
                    if num + int(freq_group_list[mess.FromQQG]) > int(frequency_additional[str(mess.FromQQG)]) or (
                            num > int(frequency_additional[str(mess.FromQQG)])):  # 大于限制频率
                        q_text.put({'mess': mess,
                                    'msg': frequency_cap_to_send.format(reset_freq_time=reset_freq_time, frequency=int(
                                        frequency_additional[str(mess.FromQQG)]),
                                                                        num=int(freq_group_list[mess.FromQQG]),
                                                                        refresh_time=round(
                                                                            reset_freq_time - (
                                                                                    time.time() - time_tmp))),
                                    'atuser': 0})
                        return
                    freq_group_list[mess.FromQQG] += num
    except:
        freq_group_list[mess.FromQQG] = num
    # --------------------------------------------------------------------------------------------------
    if before_setu_to_send_switch:
        q_text.put({'mess': mess, 'msg': before_setu_to_send, 'atuser': 0})
    setu = Setu(mess, tag, num, r18)
    setu.main()


def judgment_delay(new_group, group, time_old):  # 判断延时
    if new_group != group or time.time() - time_old >= 1.1:
        # print('{}:不延时~~~~~~~~'.format(new_group))
        return
    else:
        # print('{}:延时~~~~~~~~'.format(new_group))
        time.sleep(1.1)
        return


def sendpic_queue():
    sent_group = {'time': time.time(), 'group': 0}
    while True:
        data = q_pic.get()  # 从队列取出数据
        judgment_delay(data['mess'].FromQQG, sent_group['group'], sent_group['time'])
        send_pic(data['mess'], data['msg'], 0, data['download_url'], data['base64code'])  # 等待完成
        q_pic.task_done()
        sent_group['time'] = time.time()
        sent_group['group'] = data['mess'].FromQQG


def sendtext_queue():
    sent_group = {'time': time.time(), 'group': 0}
    while True:
        data = q_text.get()
        judgment_delay(data['mess'].FromQQG, sent_group['group'], sent_group['time'])
        send_text(data['mess'], data['msg'], data['atuser'])
        q_text.task_done()
        sent_group['time'] = time.time()
        sent_group['group'] = data['mess'].FromQQG


def heartbeat():  # 定时获取QQ连接,偶尔会突然断开
    while True:
        time.sleep(60)
        for botqq in botqqs:
            sio.emit('GetWebConn', str(botqq))  # 取得当前已经登录的QQ链接


def withdraw_queue():  # 撤回队列
    while True:
        data = q_withdraw.get()
        # withdraw_message(data['mess'])
        t = threading.Thread(target=withdraw_message,
                             args=(data['mess'],))
        t.start()
        q_withdraw.task_done()


def sentlist_clear():  # 重置发送列表
    while True:
        time.sleep(clear_sentlist_time)
        sent_list.clear()


def reset_freq_group_list():  # 重置时间
    global time_tmp
    while reset_freq_time:
        time.sleep(reset_freq_time)
        for key in freq_group_list.keys():
            freq_group_list[key] = 0
        time_tmp = time.time()


@sio.event
def connect():
    time.sleep(1)  # 等1s,不然可能连不上
    for botqq in botqqs:
        sio.emit('GetWebConn', str(botqq))  # 取得当前已经登录的QQ链接
    print('连接成功')


@sio.event
def OnGroupMsgs(message):
    # print(message)
    a = GMess(message)
    setu_keyword = setu_pattern.match(a.Content)
    if setu_keyword:
        num = setu_keyword.group(1)  # 提取数量
        tag = setu_keyword.group(2)  # 提取tag
        send_setu(a, num, tag)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        # send_text(a, msg)
        return
    # -----------------------------------------------------
    if a.At_Content == 'nmsl':
        q_text.put({'mess': a, 'msg': before_nmsl_to_send, 'atuser': 0})
        msg = nmsl()
        # send_text(a, msg)
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return
    # -----------------------------------------------------
    if RevokeMsg and a.MsgType == 'PicMsg' and (a.FromQQ in botqqs) and a.FromQQ == a.CurrentQQ:  # 是机器人发的图片就撤回
        # print(a.MsgSeq,a.MsgRandom)
        q_withdraw.put({'mess': a})
        return


@sio.event
def OnFriendMsgs(message):
    a = Mess(message)
    setu_keyword = setu_pattern.match(a.Content)
    if setu_keyword:
        num = setu_keyword.group(1)  # 提取数量
        tag = setu_keyword.group(2)  # 提取tag
        send_setu(a, num, tag)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        # send_text(a, msg)
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return
    # -----------------------------------------------------
    if a.Content == 'nmsl':
        q_text.put({'mess': a, 'msg': before_nmsl_to_send, 'atuser': 0})
        msg = nmsl()
        # send_text(a, msg)
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return


@sio.event
def OnEvents(message):
    ''' 监听相关事件'''
    # print(message)


if __name__ == '__main__':
    try:
        sio.connect(webapi, transports=['websocket'])
        beat = threading.Thread(target=heartbeat)  # 保持连接
        text_queue = threading.Thread(target=sendtext_queue)  # 文字消息队列
        pic_queue = threading.Thread(target=sendpic_queue)  # 图片消息队列
        withdrawqueue = threading.Thread(target=withdraw_queue)  # 撤回队列
        sent_list_clear = threading.Thread(target=sentlist_clear)  # 定时清除发生过的列表
        reset_freq_grouplist = threading.Thread(target=reset_freq_group_list)  # 定时清除发生过的列表
        beat.start()
        text_queue.start()
        pic_queue.start()
        withdrawqueue.start()
        sent_list_clear.start()
        reset_freq_grouplist.start()
        sio.wait()
    except BaseException as e:
        print(e)
