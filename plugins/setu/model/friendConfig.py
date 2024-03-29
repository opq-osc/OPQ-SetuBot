from typing import Literal

from pydantic import BaseModel


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


class API(BaseModel):
    lolicon: bool = True
    yuban: bool = True
    pixiv: bool = True


class Setting(BaseModel):
    setu: bool = True
    api: API = API()
    r18: bool = True
    quality: Literal["original", "large", "medium"] = "large"
    at: bool = False
    sentRefreshTime: int = 600
    singleMaximum: int = 10
    revokeTime: int = 0


class FriendConfig(BaseModel):
    setting: Setting = Setting()
    setuInfoShow: MsgShow = MsgShow()
    replyMsg: ReplyMsg = ReplyMsg()
