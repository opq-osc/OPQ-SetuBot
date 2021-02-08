from botoy import GroupMsg, FriendMsg
from botoy import decorators as deco
from loguru import logger
from module.send import Send as send
import re
import json
from module import database, config


class Cmd:
    def __init__(self, ctx):
        self.ctx = ctx
        self.msgType = ctx.type
        self.msg = ctx.Content
        self.qq = ctx.QQ
        self.qqg = ctx.QQG
        self.data = {}

    def change_dict(self, dicta, lista, change, ret=''):
        x = dicta[lista[0]]
        ret += (str(lista[0]) + ' ')
        if len(lista) == 1:
            rt_befeore = dicta.copy()
            dicta[lista[0]] = change
            return '{}: {}\n↓↓↓↓\n{}: {}'.format(ret, rt_befeore[lista[0]], ret, dicta[lista[0]])
        lista.pop(0)
        return self.change_dict(x, lista, change, ret)

    def advancedCmd(self, keyList, typ, data_str):
        if typ == 'int':
            data = int(data_str)
        elif typ == 'bool':
            data = bool(int(data_str))
        elif typ == 'str':
            data = str(data_str)
        else:
            send.text(self.ctx, '数据类型错误')
            return
        try:
            ret = self.change_dict(self.data, keyList, data)
            logger.info(ret)
            send.text(self.ctx, ret)
        except:
            send.text(self.ctx, '修改数据时出错')
            return
        database.Cmd.updateGroupData(self.qqg, self.data)

    def groupOwnerCmd(self):
        if self.msgType == 'AtMsg':
            At_Content_front = re.sub(r'@.*', '', json.loads(self.msg)['Content'])  # @消息前面的内容
            atqqs: list = json.loads(self.msg)['UserID']
            if At_Content_front == '_增加管理员':
                for qq in atqqs:
                    if qq in self.data['admins']:
                        send.text(self.ctx, '{}已经是管理员了'.format(qq))
                        continue
                    self.data['managers'].append(qq)
                    send.text(self.ctx, '管理员:{}添加成功'.format(qq))
                database.Cmd.updateGroupData(self.qqg, self.data)
            elif At_Content_front == '_删除管理员':
                for qq in atqqs:
                    try:
                        self.data['managers'].remove(qq)
                    except:
                        send.text(self.ctx, '删除{}出错'.format(qq))
                        continue
                database.Cmd.updateGroupData(self.qqg, self.data)

    def normalAdminCmd(self):
        if info := re.match('_cmd (.*)', self.msg):  # 匹配命令
            rawmsg: list = info[1].split(' ')
            cmd: str = rawmsg[0]  # 取空格前的第一个
            with open('./config/command.json', encoding='utf-8') as f:
                cmdlist = json.load(f)
            try:
                changeData = cmdlist[cmd]
            except:
                msg = '无"{}"指令'.format(cmd)
                logger.warning(msg)
                send.text(self.ctx, msg)
                return
            keylist = changeData['keyList']
            res = changeData['res']
            if res == None and len(rawmsg) == 2:  # 特殊
                if datainfo := re.match('(.*):(.*)', rawmsg[1]):
                    self.advancedCmd(keylist, datainfo[1], datainfo[2])
                    return
            try:
                send.text(self.ctx, self.change_dict(self.data, keylist, res))
            except:
                logger.warning('error: {}'.format(changeData))
                return
            database.Cmd.updateGroupData(self.qqg, self.data)

    def groupCmd(self):
        if cmdLv := self.ctx.accessLevel:
            logger.info('QQ:{} level:{}'.format(self.ctx.QQ, cmdLv))
            self.data = database.Cmd.getGroupConf(self.qqg)  # 获取群的数据
            if cmdLv == 1:
                if cmd := re.match('_advcmd (.*) (.*):(.*)', self.msg):  # 万能修改
                    self.advancedCmd(cmd[1].split(), cmd[2], cmd[3])
            if cmdLv <= 2:
                self.groupOwnerCmd()
            if cmdLv <= 3:
                self.normalAdminCmd()
            else:
                return

    def friendCmd(self):
        if res := re.match(r'_cmd [G,g] (\d+) (.*) (.*):(.*)', self.msg):  # 万能修改
            self.qqg = int(res[1])
            if self.ctx.accessLevel == 1:  # 是superadmin
                self.data = database.Cmd.getGroupConf(self.qqg)  # 获取群的数据
                self.advancedCmd(res[2].split(), res[3], res[4])

    def main(self):
        if self.msgType == 'friend':  # 好友会话
            self.friendCmd()
        elif self.msgType == 'group':  # 群聊
            self.groupCmd()
        else:
            pass


@deco.ignore_botself
@deco.in_content('_cmd')
def receive_group_msg(ctx: GroupMsg):
    Cmd(ctx).main()


@deco.ignore_botself
@deco.in_content('_cmd')
def receive_friend_msg(ctx: FriendMsg):
    Cmd(ctx).main()
