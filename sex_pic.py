from datetime import datetime
import socketio, requests, re, time, base64, random, json, psutil, cpuinfo, datetime, threading, sys, schedule
from retrying import retry
from queue import Queue, LifoQueue
from importlib import reload
import config

# -----------------------------------------------------
sio = socketio.Client()
q_pic = LifoQueue(maxsize=0)
q_text = LifoQueue(maxsize=0)
q_withdraw = Queue(maxsize=0)
# -----------------------------------------------------
api = '{}/v1/LuaApiCaller'.format(config.webapi)
groupadmins = {}  # 记录bot加的所有群的admin
sent_list = []
freq_group_list = {}
morning_list = {}
night_list = {}
time_tmp = time.time()
# -----------------------------------------------------
change_pattern = re.compile('.修改本群频率 ?(.*)')


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
        # ----------------------------------------------
        self.At_Content = ''
        self.AtUserIDs = []
        self.Content = ''
        self.At_Content_behind = ''
        self.At_Content_front = ''
        # ----------------------------------------------
        if self.MsgType == 'TextMsg':  # 普通消息
            self.Content = message['CurrentPacket']['Data']['Content']  # 消息内容
        elif self.MsgType == 'AtMsg':  # at消息
            self.At_Content = json.loads(message['CurrentPacket']['Data']['Content'])['Content']  # 完整的@消息
            self.AtUserIDs = json.loads(message['CurrentPacket']['Data']['Content'])['UserID']  # @ 的人的qq
            self.At_Content_behind = re.sub(r'.*@.* ', '', self.At_Content)  # @消息后面的内容
            self.At_Content_front = re.sub(r'@.*', '', self.At_Content)  # @消息前面的内容
            # print(self.At_Content)
            # print(self.AtUserIDs)
            # print(self.At_Content_behind)
            # print(self.At_Content_front)


class Mess:
    # 私聊消息
    def __init__(self, message):
        # print(message)
        self.messtype = 'private'  # 标记私聊
        self.CurrentQQ = message['CurrentQQ']  # 接收到这条消息的QQ
        self.QQ = message['CurrentPacket']['Data']['ToUin']  # 接收到这条消息的QQ
        self.FromQQ = message['CurrentPacket']['Data']['FromUin']  # 哪个QQ发过来的
        self.MsgType = message['CurrentPacket']['Data']['MsgType']
        self.Content = ''
        self.FromQQG = 0
        if self.MsgType == 'TextMsg':  # 普通消息
            self.Content = message['CurrentPacket']['Data']['Content']  # 消息内容
        elif self.MsgType == 'TempSessionMsg':  # 临时消息
            self.FromQQG = message['CurrentPacket']['Data']['TempUin']  # 通过哪个QQ群发起的
            self.Content = json.loads(message['CurrentPacket']['Data']['Content'])['Content']


class Event:
    # 相关事件
    def __init__(self, message):
        # print(message)
        self.messtype = 'event'  # 标记
        self.CurrentQQ = message['CurrentQQ']  # 接收到这条消息的botQQ
        self.ToUin = message['CurrentPacket']['Data']['EventMsg']['ToUin']  # 接收到这条消息的qq
        self.MsgType = message['CurrentPacket']['Data']['EventMsg']['MsgType']
        self.Content = message['CurrentPacket']['Data']['EventMsg']['Content']  # 消息内容
        self.FromQQG = message['CurrentPacket']['Data']['EventMsg']['FromUin']  # 哪个id发过来的 群号?
        self.UserID = 0
        if self.MsgType in ['ON_EVENT_GROUP_ADMIN', 'ON_EVENT_GROUP_JOIN', 'ON_EVENT_GROUP_EXIT']:  # 管理员变更
            self.UserID = message['CurrentPacket']['Data']['EventData']['UserID']  # 被操作的qq,比如成为管理员
            # self.FromQQG = message['CurrentPacket']['Data']['EventData']['GroupID']  # 哪个QQ群
            # self.Flag = message['CurrentPacket']['Data']['EventData']['Flag']  # 1为成为管理员 0是被取消管理员
        # if self.MsgType == 'ON_EVENT_GROUP_EXIT':  #退群


# --------------------------------------------------------------------------------------------------------------


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
        res = requests.post(api, params=params, json=data, timeout=8)
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
        res = requests.post(api, params=params, json=data, timeout=12)
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
    time.sleep(config.RevokeMsg_time)
    try:
        res = requests.post(api, params=params, json=data, timeout=5)
        ret = res.json()['Ret']
    except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
        ret = '超时~'
    except (ValueError, KeyError):
        ret = '返回错误~'
    except:
        ret = ("未知错误:", sys.exc_info()[0])
    print('撤回消息执行状态:[Ret:{}]'.format(ret))
    return


# --------------------------------------------------------------------------------------------------------------


class GetGroupAdmin:
    @retry(stop_max_attempt_number=3, wait_fixed=1100)
    def getGroupList(self, botqq, nextToken=''):
        global groupadmins
        while True:
            params = {'qq': botqq,
                      'funcname': 'GetGroupList'}
            data_body = {'NextToken': nextToken}
            data = requests.post(api, params=params, json=data_body, timeout=5).json()
            # print(data)
            nextToken = data['NextToken']
            for group in data['TroopList']:
                if group['GroupId'] not in groupadmins.keys():  # 不在列表里就新建,不需要处理bot被踢了的群
                    groupadmins[group['GroupId']] = [group['GroupOwner']]  # 一个群号对应一个admin列表
                else:
                    groupadmins[group['GroupId']].pop(0)  # 删掉第一个,第一个是群主
                    groupadmins[group['GroupId']].insert(0, group['GroupOwner'])  # 再插♂回去
            if nextToken == '':  # 到最后一页就停止
                break
            time.sleep(1)
        return

    @retry(stop_max_attempt_number=3, wait_fixed=1100)
    def getGroupUserList(self, botqq, groupid, lastuin=0):
        global groupadmins
        try:
            groupadmins[groupid] = groupadmins[groupid][:1]  # 清空除群主外的admin
        except:
            print('getGroupUserList :error')
            return

        while True:
            params = {'qq': botqq,
                      'funcname': 'GetGroupUserList'}
            data_body = {"GroupUin": groupid,
                         "LastUin": lastuin}
            data = requests.post(api, params=params, json=data_body, timeout=5).json()
            lastuin = data['LastUin']
            for adminqqinfo in data['MemberList']:
                if adminqqinfo['GroupAdmin'] == 1:  # 找出管理员qq并添加
                    groupadmins[groupid].append(adminqqinfo['MemberUin'])
            if lastuin == 0:
                print('群:{}的admins:{}'.format(groupid, groupadmins[groupid]))
                break
            time.sleep(1)
        return

    def main(self):
        try:
            for botqq in config.botqqs:
                self.getGroupList(botqq)
                time.sleep(1.1)
            for botqq in config.botqqs:
                for group in groupadmins.keys():
                    self.getGroupUserList(botqq, group)
                    time.sleep(1.1)
        except:
            print('获取admin失败')

# --------------------------------------------------------------------------------------------------------------


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
        if config.not_send_pic_info:
            if config.send_setu_at and self.msg_in.messtype == 'group':
                msg = '[ATUSER({qq})]'.format(qq=self.msg_in.FromQQ)
            else:
                msg = ''
        else:
            purl = "www.pixiv.net/artworks/" + str(artworkid)  # 拼凑p站链接
            uurl = "www.pixiv.net/users/" + str(artistid)  # 画师的p站链接
            page = 'p' + str(page)
            if config.send_setu_at and self.msg_in.messtype == 'group':
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
                    if filename in sent_list and config.sentlist_switch:  # 如果发送过
                        print('发送过~')
                        self.num_real -= 1
                        continue
                    url_original = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/' + filename
                    msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'], data['page'],
                                         url_original)
                    self.msg.append(msg)
                    if config.setu_path == '':  # 非本地
                        self.base64_codes.append('')
                        if config.send_original_pic:  # 发送原画
                            self.download_url.append(url_original)
                        else:
                            self.download_url.append('https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename)
                    else:  # 本地
                        self.base64_codes.append(self.base_64(config.setu_path + filename))
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
                  'apikey': config.color_pickey,
                  'num': self.api_1_num,
                  'size1200': not config.send_original_pic}
        if (len(self.tag) != 0) and (not self.tag.isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            params['keyword'] = self.tag
        try:
            res = requests.get(url, params, timeout=13)
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
                q_text.put({'mess': self.msg_in, 'msg': config.notfound_to_send, 'atuser': 0})
                # freq_group_list[self.msg_in.FromQQG] -= self.num
                return
        for i in range(len(self.msg)):
            # print('进入队列')
            q_pic.put({'mess': self.msg_in, 'msg': self.msg[i], 'download_url': self.download_url[i],
                       'base64code': self.base64_codes[i]})


def send_setu(mess, setu_keyword):
    num = setu_keyword.group(1)  # 提取数量
    tag = setu_keyword.group(2)  # 提取tag
    R18 = setu_keyword.group(3)  # 是否r18
    r18 = random.choices([0, 1], [1, 100], k=1)  # 从普通和性感中二选一
    # ------------------------------------------群聊黑白名单-------------------------------------------------------

    if mess.messtype == 'group':  # 群聊
        # print(config.group_blacklist)
        if config.group_blacklist != [] or config.group_whitelist != []:  # 如果群黑白名单中有数据
            if mess.FromQQG in config.group_blacklist:  # 如果在黑名单直接返回
                return
            if mess.FromQQG not in config.group_whitelist and config.group_whitelist != []:  # 如果不在白名单里,且白名单不为空,直接返回
                return
        if R18 != '':
            if mess.FromQQG in config.group_r18_whitelist:
                r18 = 2
            else:
                q_text.put({'mess': mess, 'msg': '本群未开启r18~', 'atuser': 0})
                return
    # ------------------------------------------临时会话黑白名单----------------------------------------------

    elif mess.messtype == 'private' and mess.FromQQG != 0:  # 临时会话
        if config.private_for_group_blacklist != [] and config.private_for_group_whitelist != []:  # 是临时会话且黑白名单中有数据
            if mess.FromQQG in config.private_for_group_blacklist:  # 如果在黑名单直接返回
                return
            if mess.FromQQG not in config.private_for_group_whitelist and config.private_for_group_whitelist != []:  # 如果不在白名单里,且白名单不为空,直接返回
                return
        if R18 != '':
            if mess.FromQQG in config.private_for_group_r18_whitelist:
                r18 = 2
            else:
                q_text.put({'mess': mess, 'msg': '本群未开启r18~', 'atuser': 0})
                return
    elif mess.FromQQG == 0 and R18 != '':  # 好友会话
        r18 = 2

    # 阿巴阿巴阿巴阿巴阿巴阿巴--------------------num部分----------------------------------------------------
    if num != '':  # 如果指定了色图数量
        try:  # 将str转换成int
            num = int(num)
            if num > config.setu_threshold:  # 如果指定数量超过设定值就返回指定消息
                # send_text(mess, threshold_to_send)
                q_text.put({'mess': mess, 'msg': config.threshold_to_send, 'atuser': 0})
                return
            if num <= 0:
                q_text.put({'mess': mess, 'msg': '¿', 'atuser': 0})
                # send_text(mess, '¿')
                return
        except:  # 如果失败了就说明不是整数数字
            # send_text(mess, wrong_input_to_send)
            q_text.put({'mess': mess, 'msg': config.wrong_input_to_send, 'atuser': 0})
            return
    else:  # 没指定的话默认是1
        num = 1
    # -----------------------------频率控制--------------------------------------------------------
    try:
        if mess.messtype == 'group':  # 只控制群聊
            if str(mess.FromQQG) not in config.frequency_additional.keys() and config.frequency != 0:  # 非自定义频率的群且限制不为0
                if (num + int(freq_group_list[mess.FromQQG])) > int(config.frequency) or (
                        num > config.frequency):  # 大于限制频率
                    q_text.put(
                        {'mess': mess,
                         'msg': config.frequency_cap_to_send.format(reset_freq_time=config.reset_freq_time,
                                                                    frequency=int(config.frequency),
                                                                    num=int(freq_group_list[
                                                                                mess.FromQQG]), refresh_time=round(
                                 config.reset_freq_time - (time.time() - time_tmp))),
                         'atuser': 0})
                    return
                freq_group_list[mess.FromQQG] += num  # 计数
            else:
                if int(config.frequency_additional[str(mess.FromQQG)]):  # 如果自定义频率不为0
                    if num + int(freq_group_list[mess.FromQQG]) > int(
                            config.frequency_additional[str(mess.FromQQG)]) or (
                            num > int(config.frequency_additional[str(mess.FromQQG)])):  # 大于限制频率
                        q_text.put({'mess': mess,
                                    'msg': config.frequency_cap_to_send.format(reset_freq_time=config.reset_freq_time,
                                                                               frequency=int(
                                                                                   config.frequency_additional[
                                                                                       str(mess.FromQQG)]),
                                                                               num=int(freq_group_list[mess.FromQQG]),
                                                                               refresh_time=round(
                                                                                   config.reset_freq_time - (
                                                                                           time.time() - time_tmp))),
                                    'atuser': 0})
                        return
                    freq_group_list[mess.FromQQG] += num
    except:
        freq_group_list[mess.FromQQG] = num
    # --------------------------------------------------------------------------------------------------
    if config.before_setu_to_send_switch:
        q_text.put({'mess': mess, 'msg': config.before_setu_to_send, 'atuser': 0})
    setu = Setu(mess, tag, num, r18)
    setu.main()


def greet(mess, flag):
    if flag:  # morning
        conf = config.morning_conf
        list_tmp = morning_list
        repeat_msg = config.morning_repeat
        num_msg_tmp = config.morning_num_msg
    else:
        conf = config.night_conf
        list_tmp = night_list
        repeat_msg = config.night_repeat
        num_msg_tmp = config.night_num_msg
    try:  # 计数
        if mess.FromQQ in list_tmp[mess.FromQQG]:  # 判断重复
            q_text.put({'mess': mess, 'msg': repeat_msg, 'atuser': 0})
            return
        list_tmp[mess.FromQQG].append(mess.FromQQ)
    except:
        list_tmp[mess.FromQQG] = [mess.FromQQ]  # 出错就说明没有这个群,添加
    num_msg = num_msg_tmp.format(num=len(list_tmp[mess.FromQQG]))  # 列表有几个qq号就是第几个
    now_time = datetime.datetime.now()  # 获取当前时间
    for msg, time_range in conf.items():
        d_time = datetime.datetime.strptime(str(now_time.date()) + time_range[0], '%Y-%m-%d%H:%M')
        d_time1 = datetime.datetime.strptime(str(now_time.date()) + time_range[1], '%Y-%m-%d%H:%M')
        if d_time > d_time1:  # 如果前面的时间大于后面的就加一天
            d_time1 = datetime.datetime.strptime(
                str((now_time + datetime.timedelta(days=1)).date()) + time_range[1], '%Y-%m-%d%H:%M')
        if d_time <= now_time < d_time1:
            q_text.put({'mess': mess, 'msg': num_msg + msg, 'atuser': 0})
            return
    q_text.put({'mess': mess, 'msg': '未匹配到时间~~', 'atuser': 0})
    return


# --------------------------------------------------------------------------------------------------------------


def reload_config():
    reload(config)
    # print('重载~')
    return


def writeJson(data):
    with open('config.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
        # print('保存')
    reload_config()


def changeAdmin(flag, mess, conf):
    reload_config()  # 重载一遍,以免手动修改的不生效
    if flag:
        for qq in mess.AtUserIDs:
            if qq not in config.config[conf]:
                config.config[conf].append(qq)
                q_text.put({'mess': mess, 'msg': '"{}"-->"{}"'.format(qq, conf), 'atuser': 0})

            else:
                q_text.put({'mess': mess, 'msg': '"{}" already in "{}"'.format(qq, conf), 'atuser': 0})
    else:
        for qq in mess.AtUserIDs:
            if qq in config.config[conf]:
                config.config[conf].remove(qq)
                q_text.put({'mess': mess, 'msg': '"{}"-->"{}"'.format(conf, qq), 'atuser': 0})

            else:
                q_text.put({'mess': mess, 'msg': '"{}" not in "{}"'.format(qq, conf), 'atuser': 0})
    writeJson(config.config)  # 写入配置


def changeOtherFreq(mess, keyword):
    reload_config()  # 重载一遍,以免手动修改的不生效
    num_str = keyword.group(1)
    try:  # 将str转换成int
        num = int(num_str)
    except:  # 如果失败了就说明不是整数数字
        # send_text(mess, wrong_input_to_send)
        q_text.put({'mess': mess, 'msg': '必须是阿拉伯数字哦', 'atuser': 0})
        return
    config.frequency_additional[str(mess.FromQQG)] = num
    writeJson(config.config)  # 写入配置
    if num == 0:
        q_text.put({'mess': mess, 'msg': '本群已取消限制~', 'atuser': 0})
        return
    q_text.put({'mess': mess, 'msg': '本群每{}s能调用{}次'.format(config.reset_freq_time, num), 'atuser': 0})
    return


def list_tf(flag, mess, conf):
    reload_config()  # 重载一遍,以免手动修改的不生效
    if mess.FromQQG != 0:  # 不为0
        groupqq = mess.FromQQG
        if flag:
            if groupqq not in config.config[conf]:
                config.config[conf].append(groupqq)
                msg = '"{}"-->"{}"'.format(groupqq, conf)
            else:
                msg = '"{}" already in "{}"'.format(groupqq, conf)
        else:  # 关闭
            if groupqq in config.config[conf]:
                config.config[conf].remove(groupqq)
                msg = '"{}"-->"{}"'.format(conf, groupqq)
            else:
                msg = '"{}" not in "{}"'.format(groupqq, conf)
        q_text.put({'mess': mess, 'msg': msg, 'atuser': 0})
        writeJson(config.config)  # 写入配置
        return


# def authentication(qq):
def command(mess):
    # print(mess.FromQQ)
    try:
        if (mess.FromQQ in groupadmins[
            mess.FromQQG]) or mess.FromQQ in config.adminQQs or mess.FromQQ == config.superAdminQQ:
            # print(type(mess.FromQQ))
            # -------------------------------------------------
            keyword_changefreq = change_pattern.match(mess.Content)
            # --------------------普通admin-------------------------
            if mess.Content == '.开启r18':
                list_tf(True, mess, 'group_r18_whitelist')
            elif mess.Content == '.关闭r18':
                list_tf(False, mess, 'group_r18_whitelist')
            elif mess.Content == '.开启私聊r18':
                list_tf(True, mess, 'private_for_group_r18_whitelist')
            elif mess.Content == '.关闭私聊r18':
                list_tf(False, mess, 'private_for_group_r18_whitelist')
            elif mess.Content == '.开启私聊':
                list_tf(False, mess, 'private_for_group_blacklist')
            elif mess.Content == '.关闭私聊':
                list_tf(True, mess, 'private_for_group_blacklist')
            elif mess.Content == '.开启色图':
                list_tf(False, mess, 'group_blacklist')
            elif mess.Content == '.关闭色图':
                list_tf(True, mess, 'group_blacklist')
            elif keyword_changefreq:
                changeOtherFreq(mess, keyword_changefreq)
            # -----------------------------------------------------
            elif mess.FromQQ == config.superAdminQQ:  # superadmin
                if mess.Content == '.reload':
                    reload_config()
                    q_text.put({'mess': mess, 'msg': '"{}" OK'.format(mess.Content), 'atuser': 0})
                # -----------------------------------------------------
                else:
                    q_text.put({'mess': mess, 'msg': '"{}" 是啥?'.format(mess.Content), 'atuser': 0})
            else:
                q_text.put({'mess': mess, 'msg': '"{}" 是啥?'.format(mess.Content), 'atuser': 0})
        else:
            q_text.put({'mess': mess, 'msg': config.Permission_denied_to_send, 'atuser': 0})
    except (ValueError, KeyError):
        print('群{}尝试重新获取admin列表'.format(mess.FromQQG))
        getgroupadmin = GetGroupAdmin()
        getgroupadmin.getGroupList(mess.CurrentQQ)
        getgroupadmin.getGroupUserList(mess.CurrentQQ, mess.FromQQG)
    except:
        print('群{}error'.format(mess.FromQQG))


def at_command(mess):
    if mess.FromQQ == config.superAdminQQ:
        if mess.At_Content_front == '.增加管理员':
            changeAdmin(True, mess, 'adminQQs')
        elif mess.At_Content_front == '.删除管理员':
            changeAdmin(False, mess, 'adminQQs')
    else:
        q_text.put({'mess': mess, 'msg': config.Permission_denied_to_send, 'atuser': 0})


# --------------------------------------------------------------------------------------------------------------
def judgment_delay(new_group, group, time_old, sleep):  # 判断延时
    if new_group != group or time.time() - time_old >= sleep:  # 如果不是相同群 或 离上次发消息已经超过1.1s就不延时
        # print('{}:不延时~~~~~~~~'.format(new_group))
        return
    else:
        # print('{}:延时~~~~~~~~'.format(new_group))
        time.sleep(sleep)
        return


def sendpic_queue():  # 图片队列
    sent_group = {'time': time.time(), 'group': 0}
    while True:
        data = q_pic.get()  # 从队列取出数据
        judgment_delay(data['mess'].FromQQG, sent_group['group'], sent_group['time'], 1.1)  # 判断是否延时
        send_pic(data['mess'], data['msg'], 0, data['download_url'], data['base64code'])  # 等待完成
        q_pic.task_done()
        '''记录时间和群号'''
        sent_group['time'] = time.time()
        sent_group['group'] = data['mess'].FromQQG


def sendtext_queue():  # 文字队列
    sent_group = {'time': time.time(), 'group': 0}
    while True:
        data = q_text.get()
        judgment_delay(data['mess'].FromQQG, sent_group['group'], sent_group['time'], 1.1)
        send_text(data['mess'], data['msg'], data['atuser'])
        q_text.task_done()
        sent_group['time'] = time.time()
        sent_group['group'] = data['mess'].FromQQG


def withdraw_queue():  # 撤回队列
    sent_group = {'time': time.time(), 'group': 0}
    while True:
        data = q_withdraw.get()
        # withdraw_message(data['mess'])
        t = threading.Thread(target=withdraw_message,
                             args=(data['mess'],))
        t.start()
        judgment_delay(data['mess'].FromQQG, sent_group['group'], sent_group['time'], 0.8)  # 判断是否延时
        q_withdraw.task_done()
        sent_group['time'] = time.time()
        sent_group['group'] = data['mess'].FromQQG


# def superadminExclusive(, ):
#     config.config['group_r18_whitelist'].remove(groupqq)


def heartbeat():  # 获取QQ连接,偶尔会突然断开
    for botqq in config.botqqs:
        sio.emit('GetWebConn', str(botqq))  # 取得当前已经登录的QQ链接
    return


def sentlist_clear():  # 重置发送列表
    sent_list.clear()
    return


def reset_freq_group_list():  # 重置时间
    global time_tmp
    if config.reset_freq_time:
        for key in freq_group_list.keys():
            freq_group_list[key] = 0
        time_tmp = time.time()
    return


def rest_greet_list():  # 清除早安晚安列表
    morning_list.clear()
    night_list.clear()
    return


def run_all_schedule():  # 运行所有定时任务
    while True:
        schedule.run_pending()
        time.sleep(0.5)


# --------------------------------------------------------------------------------------------------------------


@sio.event
def connect():
    print('开始获取bot加的所有群的管理者~~~~')
    getadmin = GetGroupAdmin()
    getadmin.main()
    # print(groupadmins)
    # time.sleep(1)  # 等1s,不然可能连不上
    for botqq in config.botqqs:
        sio.emit('GetWebConn', str(botqq))  # 取得当前已经登录的QQ链接
    print('连接成功')


@sio.event
def OnGroupMsgs(message):
    # print(message)
    a = GMess(message)
    setu_keyword = config.setu_pattern.match(a.Content)
    if setu_keyword:
        send_setu(a, setu_keyword)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        # send_text(a, msg)
        return
    # -----------------------------------------------------
    if a.At_Content_behind == 'nmsl':
        q_text.put({'mess': a, 'msg': config.before_nmsl_to_send, 'atuser': 0})
        msg = nmsl()
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return
    # -----------------------------------------------------
    if config.RevokeMsg and a.MsgType == 'AtMsg' and (
            a.FromQQ in config.botqqs) and a.FromQQ == a.CurrentQQ:  # 是机器人发的就撤回
        q_withdraw.put({'mess': a})
        return
    # -----------------------------------------------------
    if a.Content in config.morning_keyword and config.good_morning:
        greet(a, 1)
        return
    # -----------------------------------------------------
    if (a.Content in config.night_keyword) and config.good_night:
        greet(a, 0)
        return
    # ------------------------普通文字消息命令-------------------------
    if a.FromQQ not in config.botqqs:
        if a.Content[:1] == '.':
            command(a)
            return
        # ------------------------@消息命令-------------------------
        if a.At_Content[:1] == '.':
            at_command(a)
            return

        # -----------------------------------------------------


@sio.event
def OnFriendMsgs(message):
    a = Mess(message)
    setu_keyword = config.setu_pattern.match(a.Content)
    if setu_keyword:
        send_setu(a, setu_keyword)
        return
    # -----------------------------------------------------
    if a.Content == 'sysinfo':
        msg = sysinfo()
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return
    # -----------------------------------------------------
    if a.Content == 'nmsl':
        q_text.put({'mess': a, 'msg': config.before_nmsl_to_send, 'atuser': 0})
        msg = nmsl()
        q_text.put({'mess': a, 'msg': msg, 'atuser': 0})
        return


@sio.event
def OnEvents(message):
    ''' 监听相关事件'''
    a = Event(message)
    if a.MsgType == 'ON_EVENT_GROUP_ADMIN':
        print('群:{}管理员发生变更'.format(a.FromQQG))
        getgroupadmin = GetGroupAdmin()
        getgroupadmin.getGroupUserList(a.CurrentQQ, a.FromQQG)
    if (a.MsgType == 'ON_EVENT_GROUP_JOIN' and a.UserID in config.botqqs) or a.MsgType == 'ON_EVENT_GROUP_JOIN_SUCC':
        print('bot{} 加入群:{}'.format(a.UserID, a.FromQQG))
        getgroupadmin = GetGroupAdmin()
        getgroupadmin.getGroupList(a.CurrentQQ)
        getgroupadmin.getGroupUserList(a.CurrentQQ, a.FromQQG)


# --------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        sio.connect(config.webapi, transports=['websocket'])
        # -----------------------------------------------------
        text_queue = threading.Thread(target=sendtext_queue)  # 文字消息队列
        pic_queue = threading.Thread(target=sendpic_queue)  # 图片消息队列
        withdrawqueue = threading.Thread(target=withdraw_queue)  # 撤回队列
        # -----------------------------------------------------
        '''启动线程'''
        text_queue.start()
        pic_queue.start()
        withdrawqueue.start()
        # -----------------------------------------------------
        '''定时任务'''
        schedule.every(config.reset_freq_time).seconds.do(reset_freq_group_list)
        schedule.every(config.clear_sentlist_time).seconds.do(sentlist_clear)  # 定时清除发生过的列表
        schedule.every(60).seconds.do(heartbeat)  # 60s获取一次连接防止偶尔断开
        schedule.every().day.at("00:00").do(rest_greet_list)  # 0点刷新
        all_schedule = threading.Thread(target=run_all_schedule)  # 启动所有定时任务
        # -----------------------------------------------------
        all_schedule.start()
        # -----------------------------------------------------

        # -----------------------------------------------------

        sio.wait()
    except BaseException as e:
        print('boom~~~~  :{}'.format(e))
