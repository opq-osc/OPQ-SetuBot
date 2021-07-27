import json
from pathlib import Path
from typing import Literal

from botoy import Action
from loguru import logger
from pydantic import BaseModel

curFileDir = Path(__file__).absolute().parent  # 当前文件路径

with open(curFileDir.parent / "botoy.json", "r", encoding="utf-8") as f:
    botConf = json.load(f)

action = Action(qq=botConf["bot"], host=botConf["host"], port=botConf["port"])


class MsgShow(BaseModel):
    title: bool = True
    picID: bool = False
    picWebUrl: bool = True
    page: bool = True
    author: bool = True
    authorID: bool = False
    authorWebUrl: bool = True
    picOriginalUrl: bool = True
    tags: bool = True


class ReplyMsg(BaseModel):
    inputError: str = "要阿拉伯数字哦~"
    notFound: str = "你的xp好奇怪啊"
    tooMuch: str = "爪巴"
    tooSmall: str = "¿"
    closed: str = "没有,爪巴"
    noR18: str = "没有,爪巴"
    insufficient: str = "关于{tag}的图片只有{num}张"
    freqLimit: str = "本群每{time}s能发{limitCount}张色图,已发{callDone}张,离刷新还有{r_time}s"


class Switch(BaseModel):
    group: bool = True
    temp: bool = True


class Count(BaseModel):
    group: int
    temp: int


class Freq(BaseModel):
    limitCount: int = 10
    refreshTime: int = 120


class API(BaseModel):
    lolicon: bool = True
    yuban: bool = True
    pixiv: bool = True


class Setting(BaseModel):
    setu: Switch = {"group": True, "temp": True}
    api: API = API()
    r18: Switch = {"group": False, "temp": True}
    freq: Freq = Freq()
    quality: Literal["original", "large", "medium"] = "large"
    at: bool = False
    sentRefreshTime: int = 600
    singleMaximum: Count = {"group": 5, "temp": 10}
    revokeTime: Count = {"group": 20, "temp": 0}


class GroupConfig(BaseModel):
    admins: list = []
    setting: Setting = Setting()
    setuInfoShow: MsgShow = MsgShow()
    replyMsg: ReplyMsg = ReplyMsg()


if __name__ == "__main__":
    logger.info("开始更新所有群数据~")
    groupList = action.getGroupList()
    for group in groupList:
        groupid = group["GroupId"]
        filePath = (
            curFileDir.parent
            / "plugins"
            / "bot_Setu"
            / "dataBase"
            / "DB"
            / "configs"
            / "{}.json".format(groupid)
        )
        if filePath.is_file():
            logger.info("群:{} 配置文件已存在".format(groupid))
            continue
        adminList = action.getGroupAdminList(groupid)
        admins_QQid = [i["MemberUin"] for i in adminList]
        with open(filePath, "w", encoding="utf-8") as f:
            json.dump(
                GroupConfig(admins=admins_QQid).dict(), f, indent=4, ensure_ascii=False
            )
        logger.success("%s.json创建成功" % groupid)
    logger.success("更新群信息成功~")
