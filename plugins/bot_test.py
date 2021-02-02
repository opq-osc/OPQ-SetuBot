from botoy import GroupMsg, FriendMsg
from botoy.collection import MsgTypes
from botoy.decorators import ignore_botself, in_content, these_msgtypes
from botoy.refine import refine_pic_group_msg
from module.send import Send as send


@ignore_botself
@in_content("test")
def receive_group_msg(ctx: GroupMsg):
    print('111111111111111111111111111111111111')
    send.text(ctx, '????????')


@ignore_botself
@in_content("test")
def receive_friend_msg(ctx: FriendMsg):
    print('?????????????????????????')
    send.text(ctx, '????????')
