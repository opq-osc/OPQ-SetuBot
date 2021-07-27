import json
import re
from pathlib import Path

from botoy import GroupMsg, S, jconfig
from loguru import logger

from ..bot_Setu.dataBase import getGroupConfig
from ..bot_Setu.model import GroupConfig

curFileDir = Path(__file__).absolute().parent  # 当前文件路径


class CMD:
    def __init__(self, ctx: GroupMsg):
        self.ctx = ctx
        self.send = S.bind(self.ctx)
        self.config: dict

    def write_group_config(self, groupid):
        try:
            data = GroupConfig(**self.config).dict()
        except Exception as e:
            logger.error("数据类型检查错误\r\n%s" % e)
            return False
        try:
            with open(
                curFileDir.parent
                / "bot_Setu"
                / "dataBase"
                / "DB"
                / "configs"
                / "{}.json".format(groupid),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("写入{}.json成功".format(groupid))
            return True
        except Exception as e:
            logger.error("写入{}.json失败\r\n{}".format(groupid, e))
            return False

    def change_dict(self, dicta: dict, lista: list, change, ret=""):
        """
        按照传入的keylist顺序修改value的值位change
        :param dicta: 要修改的dict
        :param lista: key的顺序
        :param change: 要修改的值
        :param ret: 占位
        :return:
        """
        x = dicta[lista[0]]
        ret += str(lista[0]) + " "
        if len(lista) == 1:
            rt_befeore = dicta.copy()
            dicta[lista[0]] = change
            return "{}: {}-{}\n↓↓↓↓\n{}: {}-{}".format(
                ret,
                rt_befeore[lista[0]],
                type(rt_befeore[lista[0]]),
                ret,
                dicta[lista[0]],
                type(dicta[lista[0]]),
            )
        lista.pop(0)
        return self.change_dict(x, lista, change, ret)

    def advanced_command(self, groupid, keyList, typ, data_str):
        """
        高级命令
        :return:
        """
        try:
            if typ == "int":
                data = int(data_str)
            elif typ == "bool":
                data = bool(int(data_str))
            elif typ == "str":
                data = str(data_str)
            else:
                self.send.text("不支持此数据类型")
                return
        except:
            self.send.text("数据类型转换错误")
            return
        try:
            ret = self.change_dict(self.config, keyList, data)
            logger.info(ret)
        except:
            logger.error("修改数据出错{}    {}".format(keyList, data))
            self.send.text("修改数据时出错")
            return
        if self.write_group_config(groupid):
            self.send.text(ret)
        else:
            self.send.text("写入数据错误,请查看日志")
            return

    def specific_command(self, info):
        """
        中文的特定命令
        :param info
        :return:
        """
        rawmsg: list = info[1].split(" ")
        cmd: str = rawmsg[0]  # 取空格前的第一个
        with open(curFileDir / "command.json", encoding="utf-8") as f:
            cmdlist = json.load(f)
        try:
            changeData = cmdlist[cmd]
        except:
            msg = '无"{}"指令'.format(cmd)
            logger.warning(msg)
            self.send.text(msg)
            return
        keylist = changeData["keyList"]
        res = changeData["res"]
        if res == None and len(rawmsg) == 2:  # 特殊
            if datainfo := re.match("(.*):(.*)", rawmsg[1]):
                self.advanced_command(self.ctx.QQG, keylist, datainfo[1], datainfo[2])
                return
        try:
            ret = self.change_dict(self.config, keylist, res)
        except:
            logger.warning("error: {}".format(changeData))
            return
        if self.write_group_config(self.ctx.QQG):
            self.send.text(ret)
        else:
            self.send.text("写入数据错误,请查看日志")
            return

    def auth(self):
        """
        鉴权
        :return:
        """
        if self.ctx.QQ == jconfig.superAdmin:
            return 1
        if self.ctx.QQ in self.config.admins:
            return 2
        return False

    def main(self):
        if auth := self.auth():
            if auth == 1:
                if res := re.match(
                    r"_cmd [G,g] (\d+) (.*) (.*):(.*)", self.ctx.Content
                ):  # 万能修改
                    self.config = getGroupConfig(int(res[1])).dict()  # 获取群的数据
                    self.advanced_command(int(res[1]), res[2].split(), res[3], res[4])
            self.config = getGroupConfig(self.ctx.QQG).dict()  # 获取群的数据
            if res := re.match(r"_cmd_adv (.*) (.*):(.*)", self.ctx.Content):  # 万能修改
                self.advanced_command(self.ctx.QQG, res[1].split(), res[2], res[3])
            if self.ctx.type != "friend":
                if res := re.match("_cmd (.*)", self.ctx.Content):  # 匹配命令
                    self.specific_command(res)
        else:
            return
