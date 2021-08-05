import random
import re
import time
from pathlib import Path

from loguru import logger
from tinydb import TinyDB, where

curFileDir = Path(__file__).absolute().parent  # 当前文件路径
setuDB = TinyDB(curFileDir / "DB" / "setu.json")


class LocalSetu:
    @staticmethod
    def conversionLevel(level_int):
        conversionDict = {0: "normal", 1: "sexy", 2: "porn", 3: "all"}
        return conversionDict[level_int]

    @classmethod
    def addSetu(cls, data: dict, level: int, groupid: int):  # 改成单个插入 由上级控制 ,群独立
        typE = cls.conversionLevel(level)
        data["time"] = int(time.time())
        if res := setuDB.get(
            (where("artwork") == data["artwork"]) & (where("page") == data["page"])
        ):  # 数据库有数据
            data["type"] = res["type"]
            for k, v in data[
                "type"
            ].items():  # 遍历 'type': {'normal': [], 'sexy': [], 'porn': []}
                if k != typE:  # 群号出现在非这次修改的等级里
                    if groupid in v:
                        data["type"][k].remove(groupid)
                else:
                    data["type"][k].append(groupid)
                data["type"][k] = list(set(data["type"][k]))  # 以防万一,去重
            setuDB.update(
                data,
                (where("artwork") == data["artwork"]) & (where("page") == data["page"]),
            )
            logger.info(
                "pid:{} page:{} group:{}-->{}".format(
                    data["artwork"], data["page"], res["type"], data["type"]
                )
            )
        else:
            data["type"][typE].append(groupid)
            setuDB.insert(data)
            logger.info(
                "pid:{} page:{} group:{}".format(
                    data["artwork"], data["page"], data["type"]
                )
            )
        # return '群{}:{}添加成功,图片分级{}'.format(groupid, data['original'],typE)

    @staticmethod
    def delSetu(artworkid, groupid, page: int = None):
        if page == None:
            if res := setuDB.search(
                (where("artwork") == artworkid)
                & (
                    (where("type")["normal"].any([groupid]))
                    | (where("type")["sexy"].any([groupid]))
                    | (where("type")["porn"].any([groupid]))
                )
            ):  # 数据库有数据
                for data in res:
                    for k, v in data["type"].items():
                        if groupid in v:
                            data["type"][k].remove(groupid)
                    setuDB.update(
                        data,
                        (where("artwork") == artworkid)
                        & (where("page") == data["page"]),
                    )
                return True
            else:
                return False
        else:
            if res := setuDB.get(
                (where("artwork") == artworkid)
                & (where("page") == page)
                & (
                    (where("type")["normal"].any([groupid]))
                    | (where("type")["sexy"].any([groupid]))
                    | (where("type")["porn"].any([groupid]))
                )
            ):  # 数据库有数据
                for k, v in res["type"].items():
                    if groupid in v:
                        res["type"][k].remove(groupid)
                setuDB.update(
                    res, (where("artwork") == artworkid) & (where("page") == page)
                )
                return True
            else:
                return False

    @staticmethod
    def updateSetu(artworkid, page, data):
        setuDB.update(data, (where("artwork") == artworkid & where("page") == page))

    @classmethod
    def _serchtags(cls, taglist: list, expr=None):
        # print(taglist)
        if not taglist:
            return expr
        if expr:
            expr = expr & (
                where("tags").any((where("name").matches(taglist[0], re.I | re.M)))
            )
        else:
            expr = where("tags").any((where("name").matches(taglist[0], re.I | re.M)))
        taglist.pop(0)
        return cls._serchtags(taglist, expr)

    @classmethod
    def getSetu(
        cls, groupid: int, level: int, num: int, tags: list
    ):  # 用lv做key   {lv:[{'sexy':[0,123]},]}
        tags = tags.copy()  # 有bug,递归会把上层的也删掉
        level = cls.conversionLevel(level)  # 转换
        for i in range(len(tags)):
            tags[i] = ".*{}".format(tags[i])
        if level != "all":  # 指定setu等级
            allTagList = ["normal", "sexy", "porn"]
            allTagList.remove(level)
            if tags:
                data = setuDB.search(
                    (~where("type")[allTagList[0]].any([groupid]))
                    & (~where("type")[allTagList[1]].any([groupid]))
                    & (where("type")[level].any([0, groupid]))
                    & cls._serchtags(tags)
                )
            else:
                data = setuDB.search(
                    (~where("type")[allTagList[0]].any([groupid]))
                    & (~where("type")[allTagList[1]].any([groupid]))
                    & (where("type")[level].any([0, groupid]))
                )
        else:  # 从全部色图中搜索
            if tags:
                data = setuDB.search(
                    (
                        (where("type")["normal"].any([0, groupid]))
                        | (where("type")["sexy"].any([0, groupid]))
                        | (where("type")["porn"].any([0, groupid]))
                    )
                    & (cls._serchtags(tags))
                )
            else:
                data = setuDB.search(
                    (
                        (where("type")["normal"].any([0, groupid]))
                        | (where("type")["sexy"].any([0, groupid]))
                        | (where("type")["porn"].any([0, groupid]))
                    )
                )
        if len(data) <= num:
            return data
        return random.sample(data, num)
