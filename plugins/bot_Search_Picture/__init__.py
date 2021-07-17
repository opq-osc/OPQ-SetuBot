"""
CMD:
?????????
"""
from botoy import MsgTypes
from botoy import decorators as deco
from .searchPicture import SearchPic


@deco.ignore_botself
@deco.in_content('.*搜图')
@deco.these_msgtypes(MsgTypes.PicMsg)
def receive_group_msg(ctx):
    SearchPic(ctx).main()


@deco.ignore_botself
@deco.in_content('.*搜图')
@deco.these_msgtypes(MsgTypes.PicMsg)
def receive_friend_msg(ctx):
    SearchPic(ctx).main()
