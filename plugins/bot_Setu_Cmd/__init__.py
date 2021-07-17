"""
CMD:
?????????
"""
from botoy import FriendMsg, GroupMsg
from botoy import decorators as deco
from .command import CMD





@deco.ignore_botself
@deco.in_content('_cmd')
def receive_group_msg(ctx: GroupMsg):
    CMD(ctx).main()


@deco.ignore_botself
@deco.in_content('_cmd')
def receive_friend_msg(ctx: FriendMsg):
    CMD(ctx).main()
