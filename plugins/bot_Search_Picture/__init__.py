from botoy import MsgTypes
from botoy import decorators as deco

from .searchPicture import SearchPic

__doc__ = """把文字:"搜图"和图片放在一条消息中即可搜图"""


main = lambda ctx: SearchPic(ctx).main()


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.PicMsg)
@deco.in_content(".*搜图")
def receive_group_msg(ctx):
    main(ctx)


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.PicMsg)
@deco.in_content(".*搜图")
def receive_friend_msg(ctx):
    main(ctx)
