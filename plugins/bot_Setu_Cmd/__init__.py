from botoy import FriendMsg, GroupMsg
from botoy import decorators as deco

from .command import CMD

__doc__ = """使用命令方便的修改色图插件的配置文件"""


@deco.in_content("_cmd")
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    CMD(ctx).main()


@deco.in_content("_cmd")
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):
    CMD(ctx).main()
