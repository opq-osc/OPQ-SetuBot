import re
from pathlib import Path

import ujson as json
from botoy import logger, contrib

from ..database import getGroupConfig, updateGroupConfig

curFileDir = Path(__file__).parent  # 当前文件路径


class CMD:
    def __init__(self, S, groupid, cmd):
        self.S = S
        self.cmd_text = cmd
        self.groupid = groupid
        self.config: dict = None

    def change_dict(self, dicta: dict, lista: list, change, ret=""):
        """
        按照传入的keylist顺序修改value的值为change
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

    async def advanced_command(self, groupid, keyList, typ, data_str):
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
                await self.S.text("不支持此数据类型")
                return
        except:
            await self.S.text("数据类型转换错误")
            return
        try:
            ret = self.change_dict(self.config, keyList, data)
            logger.info(ret)
        except:
            logger.error("修改数据出错{}    {}".format(keyList, data))
            await self.S.text("修改数据时出错")
            return
        if await updateGroupConfig(groupid, self.config):
            await self.S.text(ret)
        else:
            await self.S.text("写入数据错误,请查看日志")
            return

    @contrib.to_async
    def get_cmdlist(self):
        with open(curFileDir / "command.json", encoding="utf-8") as f:
            cmdlist = json.load(f)
        return cmdlist

    async def specific_command(self, info):
        """
        中文的特定命令
        :param info
        :return:
        """
        rawmsg: list = info.split(" ")
        cmd: str = rawmsg[0]  # 取空格前的第一个
        cmdlist = await self.get_cmdlist()
        try:
            changeData = cmdlist[cmd]
        except:
            msg = '无"{}"指令'.format(cmd)
            logger.warning(msg)
            await self.S.text(msg)
            return
        keylist = changeData["keyList"]
        res = changeData["res"]
        if res == None and len(rawmsg) == 2:  # 特殊
            if datainfo := re.match("(.*):(.*)", rawmsg[1]):
                await self.advanced_command(
                    self.groupid, keylist, datainfo[1], datainfo[2]
                )
                return
        try:
            ret = self.change_dict(self.config, keylist, res)
        except:
            logger.warning("error: {}".format(changeData))
            return
        if await updateGroupConfig(self.groupid, self.config):
            await self.S.text(ret)
        else:
            await self.S.text("写入数据错误,请查看日志")
            return

    async def main(self):
        if config := await getGroupConfig(self.groupid):
            self.config = config.dict()
        else:
            await self.S.text("无配置文件")
            return
        await self.specific_command(self.cmd_text)
