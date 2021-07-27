from botoy import MsgTypes
from botoy import decorators as deco

from .searchPicture import SearchPic

__doc__ = """把文字:"搜图"和图片放在一条消息中即可"""


@deco.these_msgtypes(MsgTypes.PicMsg)
@deco.in_content(".*搜图")
@deco.ignore_botself
def receive_group_msg(ctx):
    searchPic = SearchPic(ctx)
    searchPic.main()
    del searchPic


@deco.these_msgtypes(MsgTypes.PicMsg)
@deco.in_content(".*搜图")
@deco.ignore_botself
def receive_friend_msg(ctx):
    searchPic = SearchPic(ctx)
    searchPic.main()
    del searchPic
