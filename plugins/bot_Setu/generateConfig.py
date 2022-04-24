import json
from pathlib import Path
from typing import Literal

from botoy import Action
from loguru import logger
from pydantic import BaseModel

curFileDir = Path(__file__).absolute().parent  # 当前文件路径

with open(curFileDir.parent / "botoy.json", "r", encoding="utf-8") as f:
    botConf = json.load(f)

action = Action(qq=botConf["bot"], host=botConf["host"], port=8892)


class MsgShow(BaseModel):
    title: bool = False
    picID: bool = False
    picWebUrl: bool = False
    page: bool = False
    author: bool = False
    authorID: bool = False
    authorWebUrl: bool = False
    picOriginalUrl: bool = False
    tags: bool = False


class ReplyMsg(BaseModel):
    inputError: str = "要阿拉伯数字哦~"
    notFound: str = "你的xp好奇怪啊"
    tooMuch: str = "你要这么多色图怎么不冲死"
    tooSmall: str = "¿"
    closed: str = "没有,爪巴"
    noR18: str = "没有,爪巴"
    insufficient: str = "关于{tag}的图片只有{num}张"
    freqLimit: str = "本群每{time}s能发{limitCount}张色图,已发{callDone}张,离刷新还有{r_time}s"


class Switch(BaseModel):
    group: bool = True
    temp: bool = False


class Count(BaseModel):
    group: int
    temp: int


class Freq(BaseModel):
    limitCount: int = 6
    refreshTime: int = 600


class API(BaseModel):
    lolicon: bool = True
    yuban: bool = True
    pixiv: bool = True


class Setting(BaseModel):
    setu: Switch = {"group": True, "temp": True}
    api: API = API()
    r18: Switch = {"group": False, "temp": True}
    freq: Freq = Freq()
    quality: Literal["original", "large", "medium"] = "medium"
    at: bool = False
    sentRefreshTime: int = 1296000
    singleMaximum: Count = {"group": 5, "temp": 0}
    revokeTime: Count = {"group": 0, "temp": 0}


class GroupConfig(BaseModel):
    admins: list = []
    setting: Setting = Setting()
    setuInfoShow: MsgShow = MsgShow()
    replyMsg: ReplyMsg = ReplyMsg()


def geneConfig(group):
    logger.info("开始更新本群数据~")
    groupid = group
    filePath = (
        curFileDir.parent
        / "bot_Setu"
        / "database"
        / "DB"
        / "configs"
        / "{}.json".format(groupid)
    )
    if filePath.is_file():
        logger.info("群:{} 配置文件已存在".format(groupid))
       # continue
    adminList = action.getGroupAdminList(groupid)
    admins_QQid = [i["MemberUin"] for i in adminList]
    with open(filePath, "a+", encoding="utf-8") as f:
        json.dump(
            GroupConfig( admins=admins_QQid).dict(),f, indent=4, ensure_ascii=False
        )
    logger.success("%s.json创建成功" % groupid)
logger.success("更新群信息成功~")

