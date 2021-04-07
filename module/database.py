from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage
from tinydb.operations import add
from loguru import logger
from module.send import action
from module import config
import os
import time
import re
import random
from retrying import retry

groupConfig = TinyDB('./config/groupConfig.json')
friendConfig = TinyDB('./config/friendConfig.json')
setuTagConfig = TinyDB('./config/setuTagConfig.json')
lotteryData = TinyDB('./config/lotteryData.json')
setuDB = TinyDB('./config/setu.json')

tmpDB = TinyDB(storage=MemoryStorage)


# Q = Query()


# todo: 创建一个数据库的基本操作类,接下来各个模块的小类全部继承这个base类

#
# def matches_regex(values, pattern):
#     # return any(re.match(pattern, value) for value in values)
#     for v in values:
#         print(v)


class BasicOperation:

    @staticmethod
    def change_dict(dicta, lista, change, ret=''):
        x = dicta[lista[0]]
        ret += (str(lista[0]) + ' ')
        if len(lista) == 1:
            rt_befeore = dicta.copy()
            dicta[lista[0]] = change
            return '{}: {}\n↓↓↓↓\n{}: {}'.format(ret, rt_befeore[lista[0]], ret, dicta[lista[0]])
        lista.pop(0)
        return BasicOperation.change_dict(x, lista, change, ret)

    @staticmethod
    def auth(qqg: int, qq: int):  # superadmin:1 ,群主:2 , 管理员:3
        if qq == config.superadmin:
            return 1
        elif res := groupConfig.get(where('GroupId') == qqg):
            if qq == res['GroupOwner']:
                return 2
            elif qq in res['admins'] or qq in res['managers']:  # 管理员
                return 3
            else:
                return 0
        else:
            return 0

    @staticmethod
    def updateGroupData(groupid: int, data: dict):
        groupConfig.update(data, where('GroupId') == groupid)

    @staticmethod
    def getGroupConf(groupid: int):
        return groupConfig.get(where('GroupId') == groupid)

    @staticmethod
    def getUserconf(userid: int):
        if conf := friendConfig.get(where('QQ') == userid):
            return conf
        else:
            return {
                'setuinfo': {
                    'title': True,
                    'pid': False,
                    'purl': True,
                    'page': True,
                    'author': True,
                    'uurl': True,
                    'uid': False,
                    'url_original': True,
                    # '': True,
                    # '': True,
                    # '': True
                },
                'original': False,
                'setuLevel': 1,
                'refreshSent': 600,
                'at': False,
                'at_warning': False,  # @
                'returnTags': True,
                'msg_inputError': '必须是正整数数字哦~',  # 非int
                'msg_notFind': '你的xp好奇怪啊',  # 没结果
                'msg_tooMuch': '爪巴',  # 大于最大值
                'msg_lessThan0': '¿¿¿',  # 小于0
                'msg_setuClosed': 'setu已关闭~',
                'msg_r18Closed': '未开启r18~',
                'msg_insufficient': '关于{tag}的图片只获取到{num}张'
            }


class LocalSetu:

    @staticmethod
    def conversionLevel(level_int):
        conversionDict = {0: 'normal',
                          1: 'sexy',
                          2: 'porn',
                          3: 'all'}
        return conversionDict[level_int]

    @classmethod
    def addSetu(cls, data: dict, level: int, groupid: int):  # 改成单个插入 由上级控制 ,群独立
        typE = cls.conversionLevel(level)
        data['time'] = int(time.time())
        if res := setuDB.get((where('artwork') == data['artwork']) & (where('page') == data['page'])):  # 数据库有数据
            data['type'] = res['type']
            for k, v in data['type'].items():  # 遍历 'type': {'normal': [], 'sexy': [], 'porn': []}
                if k != typE:  # 群号出现在非这次修改的等级里
                    if groupid in v:
                        data['type'][k].remove(groupid)
                else:
                    data['type'][k].append(groupid)
                data['type'][k] = list(set(data['type'][k]))  # 以防万一,去重
            setuDB.update(data, (where('artwork') == data['artwork']) & (where('page') == data['page']))
            logger.info(
                'pid:{} page:{} group:{}-->{}'.format(data['artwork'], data['page'], res['type'], data['type']))
        else:
            data['type'][typE].append(groupid)
            setuDB.insert(data)
            logger.info('pid:{} page:{} group:{}'.format(data['artwork'], data['page'], data['type']))
        # return '群{}:{}添加成功,图片分级{}'.format(groupid, data['original'],typE)

    @staticmethod
    def delSetu(artworkid, groupid, page: int = None):
        if page == None:
            if res := setuDB.search((where('artwork') == artworkid) &
                                    (
                                            (where('type')['normal'].any([groupid])) |
                                            (where('type')['sexy'].any([groupid])) |
                                            (where('type')['porn'].any([groupid]))
                                    )):  # 数据库有数据
                for data in res:
                    for k, v in data['type'].items():
                        if groupid in v:
                            data['type'][k].remove(groupid)
                    setuDB.update(data, (where('artwork') == artworkid) & (where('page') == data['page']))
                return True
            else:
                return False
        else:
            if res := setuDB.get((where('artwork') == artworkid) &
                                 (where('page') == page) &
                                 (
                                         (where('type')['normal'].any([groupid])) |
                                         (where('type')['sexy'].any([groupid])) |
                                         (where('type')['porn'].any([groupid]))
                                 )):  # 数据库有数据
                for k, v in res['type'].items():
                    if groupid in v:
                        res['type'][k].remove(groupid)
                setuDB.update(res, (where('artwork') == artworkid) & (where('page') == page))
                return True
            else:
                return False

    @staticmethod
    def updateSetu(artworkid, page, data):
        setuDB.update(data, (where('artwork') == artworkid & where('page') == page))

    @classmethod
    def _serchtags(cls, taglist: list, expr=None):
        # print(taglist)
        if not taglist:
            return expr
        if expr:
            expr = expr & (where('tags').any((where('name').matches(taglist[0], re.I | re.M))))
        else:
            expr = where('tags').any((where('name').matches(taglist[0], re.I | re.M)))
        taglist.pop(0)
        return cls._serchtags(taglist, expr)

    @classmethod
    def getSetu(cls, groupid: int, level: int, num: int, tags: list):  # 用lv做key   {lv:[{'sexy':[0,123]},]}
        tags = tags.copy()  # 有bug,递归会把上层的也删掉
        level = cls.conversionLevel(level)  # 转换
        for i in range(len(tags)):
            tags[i] = '.*{}'.format(tags[i])
        if level != 'all':  # 指定setu等级
            allTagList = ['normal', 'sexy', 'porn']
            allTagList.remove(level)
            if tags:
                data = setuDB.search(
                    (~where('type')[allTagList[0]].any([groupid])) &
                    (~where('type')[allTagList[1]].any([groupid])) &
                    (where('type')[level].any([0, groupid])) &
                    cls._serchtags(tags)
                )
            else:
                data = setuDB.search(
                    (~where('type')[allTagList[0]].any([groupid])) &
                    (~where('type')[allTagList[1]].any([groupid])) &
                    (where('type')[level].any([0, groupid]))
                )
        else:  # 从全部色图中搜索
            if tags:
                data = setuDB.search(
                    (
                            (where('type')['normal'].any([0, groupid])) |
                            (where('type')['sexy'].any([0, groupid])) |
                            (where('type')['porn'].any([0, groupid]))
                    )
                    & (cls._serchtags(tags))
                )
            else:
                data = setuDB.search(
                    (
                            (where('type')['normal'].any([0, groupid])) |
                            (where('type')['sexy'].any([0, groupid])) |
                            (where('type')['porn'].any([0, groupid]))
                    )
                )
        if len(data) <= num:
            return data
        return random.sample(data, num)


class Cmd(BasicOperation):
    pass
    #
    # @staticmethod
    # def getGroupData(qqg):
    #     return groupConfig.get(Q['GroupId'] == qqg)


class Setu(BasicOperation):

    @staticmethod
    def ifSent(ID, url, refreshTime):
        filename = os.path.basename(url)
        if data := tmpDB.table('sentlist').search((where('id') == ID) & (where('filename') == filename)):  # 如果有数据
            if time.time() - data[0]['time'] <= refreshTime:  # 发送过
                logger.info('id:{},{}发送过~'.format(ID, filename))
                return True
            else:
                tmpDB.table('sentlist').update({'time': time.time()},
                                               (where('id') == ID) & (where('filename') == filename))
                return False
        else:  # 没数据
            tmpDB.table('sentlist').insert({'id': ID, 'time': time.time(), 'filename': filename})
            return False

    @staticmethod
    def freq(groupid, num, refreshTime, freqCount):
        if data_tmp := tmpDB.table('freq').get(where('group') == groupid):  # 如果有数据
            if refreshTime != 0 and (time.time() - data_tmp['time'] >= refreshTime):  # 刷新
                tmpDB.table('freq').update({'time': time.time(), 'freq': 0}, where('group') == groupid)
                return False
            elif freqCount != 0 and num + data_tmp['freq'] > freqCount:  # 大于限制且不为0
                logger.info('群:{}大于频率限制:{}次/{}s'.format(groupid, freqCount, refreshTime))
                return freqCount,  data_tmp['time']
            # 记录
            tmpDB.table('freq').update(add('freq', num), where('group') == groupid)
        else:  # 没数据
            logger.info('群:{}第一次调用'.format(groupid))
            tmpDB.table('freq').insert({'group': groupid, 'time': time.time(), 'freq': num})
        return False

    @staticmethod
    def getGroupConf(groupid: int, msgType: str):
        # data = {}
        if res := groupConfig.get(where('GroupId') == groupid):
            for k, v in res.items():
                # print(k, v)
                if type(v) == dict:
                    try:
                        res[k] = v[msgType]
                    except:
                        pass
                        # data[str(k)] = v
            # print(res)
            return res


class Lottery:
    @staticmethod
    def getUserInfo(qq: int, conf: dict, pool: str):
        if res := lotteryData.table(pool).get(where('qq') == qq):
            return res
        else:
            data = {
                'qq': qq,
                'allCount': 0,  # 总次数
                'farFiveStarFloors': conf[pool]['fiveStarFloorsCount'],  # 离5星保底次数
                'farFourStarFloors': conf[pool]['fourStarFloorsCount'],  # 离4星保底次数
                'FiveStarFloorsCount': 0,  # 5星保底数
                'FourStarFloorsCount': 0,  # 4星保底数
                'FiveStarCount': 0,  # 获取到的5星数量
                'FourStarCount': 0,  # 获取到的4星数量
                'certainlyFiveStarUp': False,  # 必定5星up
                'certainlyFourStarUp': False,  # 必定4星up
            }
            lotteryData.table(pool).insert(data)
            return data

    @staticmethod
    def updateUserinfo(qq, pool, data):
        lotteryData.table(pool).update(data, where('qq') == qq)


class Event:
    @staticmethod
    def changeGroupAdmin(group: int, admins: list, flag: bool):
        pass

    @staticmethod
    def changeGroupManager(group: int, managers: list, flag: bool):
        pass

    @staticmethod
    def updateAdminAndManager(groupid: int, admins: list, managers: list):
        groupConfig.update({'admins': admins, 'managers': managers}, where('GroupId') == groupid)
    # @staticmethod
    # def


class Getdata:
    @staticmethod
    def defaultdata(data):
        data['managers'] = []  # 所有的管理者(可以设置bot功能的)
        # -----------------------------------------------------
        data['setuLevel'] = {'group': 1, 'temp': 3}  # 默认等级 0:正常 1:性感 2:色情 3:All
        data['setuinfo'] = {
            'title': True,
            'pid': False,
            'purl': True,
            'page': True,
            'author': True,
            'uurl': True,
            'uid': False,
            'url_original': True,
            # '': True
        }
        data['returnTags'] = True  # 显示tag
        data['original'] = {'group': False, 'temp': False}  # 是否原图
        data['setu'] = {'group': True, 'temp': True}  # 色图功能开关
        data['r18'] = {'group': False, 'temp': True}  # 是否开启r18
        data['freq'] = 10  # 频率 (次)
        data['refreshTime'] = 60  # 刷新时间 (s)
        data['refreshSent'] = 900  # 刷新sent时间 (s)
        data['maxnum'] = {'group': 3, 'temp': 10}  # 一次最多数量
        data['msgCount'] = {'text': 0, 'pic': 0, 'voice': 0}  # 消息数量
        data['revoke'] = {'group': 20, 'temp': 0}  # 撤回消息延时(0为不撤回)
        data['at'] = False  # @
        data['at_warning'] = False  # @
        data['msg_inputError'] = '必须是正整数数字哦~'  # 非int
        data['msg_notFind'] = '你的xp好奇怪啊'  # 没结果
        data['msg_tooMuch'] = '爪巴'  # 大于最大值
        data['msg_lessThan0'] = '¿¿¿'  # 小于0
        data['msg_setuClosed'] = 'setu已关闭~'
        data['msg_r18Closed'] = '未开启r18~'
        data['msg_insufficient'] = '关于{tag}的图片只获取到{num}张'
        data['msg_frequency'] = '本群每{time}s能调用{num}次,已经调用{num_call}次,离刷新还有{r_time}s'
        # data['msg_'] = ''
        # return data

    @classmethod
    def updateData(cls, data, groupid):
        if groupConfig.search(where('GroupId') == groupid):
            logger.info('群:{}已存在,更新数据~'.format(groupid))
            groupConfig.update(data, where('GroupId') == groupid)
        else:
            cls.defaultdata(data)
            logger.info('群:{}不存在,插入数据~'.format(groupid))
            groupConfig.insert(data)

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateAllGroupData(self):
        logger.info('开始更新所有群数据~')
        data = action.getGroupList()
        allgroups_get = [x['GroupId'] for x in data]
        for group in data:
            del group['GroupNotice']  # 删除不需要的key
            admins = action.getGroupAdminList(group['GroupId'])
            admins_QQid = [i['MemberUin'] for i in admins]
            group['admins'] = admins_QQid  # 管理员列表
            self.updateData(group, group['GroupId'])
        allgroups_db = [i['GroupId'] for i in groupConfig.all()]
        if extraGroup := list(set(allgroups_db).difference(set(allgroups_get))):  # 多余的群
            logger.info('数据库中多余群:{}'.format(extraGroup))
            for groupid_del in extraGroup:
                groupConfig.remove(where('GroupId') == groupid_del)
                logger.info('已删除群:{}数据'.format(groupid_del))
        logger.success('更新群信息成功~')
        return

    @classmethod
    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateGroupData(cls, groupid: int):
        logger.info('开始刷新群:{}的数据'.format(groupid))
        data = action.getGroupList()
        for group in data:
            if group['GroupId'] == groupid:
                del group['GroupNotice']  # 删除不需要的key
                admins = action.getGroupAdminList(groupid)
                admins_QQid = [i['MemberUin'] for i in admins]
                group['admins'] = admins_QQid
                logger.info('群:{}的admins:{}'.format(groupid, admins_QQid))
                cls.updateData(group, group['GroupId'])
                return
        logger.warning('群:{}不存在~'.format(groupid))
