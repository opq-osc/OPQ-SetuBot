from botoy import MsgTypes
from botoy import async_decorators as deco

from .searchPicture import SearchPic

__doc__ = """把文字:"搜图"和图片放在一条消息中即可搜图"""


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.PicMsg)
@deco.in_content(".*搜图")
async def main(ctx):
    await SearchPic(ctx).main()


receive_group_msg = receive_friend_msg = main
