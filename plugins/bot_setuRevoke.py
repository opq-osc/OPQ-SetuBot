import random
import re
import time

from botoy import Action, GroupMsg, FriendMsg
from botoy.decorators import from_botself


@from_botself
def main(ctx: GroupMsg):
    if not "REVOKE" in ctx.Content:
        return
    if delay := re.findall(r"REVOKE\[(\d+)]", ctx.Content):
        delay = min(int(delay[0]), 90)
    else:
        delay = random.randint(30, 60)

    time.sleep(delay)

    Action(
        ctx.CurrentQQ,
        host=getattr(ctx, "_host", None),
        port=getattr(ctx, "_port", None),
    ).revokeGroupMsg(ctx.QQG, ctx.MsgSeq, ctx.MsgRandom)


def receive_group_msg(ctx: GroupMsg):
    main(ctx)
