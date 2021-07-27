import random
import re
import time

from botoy import Action, GroupMsg
from botoy.decorators import from_botself


@from_botself
def receive_group_msg(ctx: GroupMsg):
    if not "REVOKE" in ctx.Content:
        return

    if delay := re.findall(r"REVOKE\[(\d+)\]", ctx.Content):
        delay = min(int(delay[0]), 90)
    else:
        delay = random.randint(30, 60)

    time.sleep(delay)

    Action(
        ctx.CurrentQQ,
        host=getattr(ctx, "_host", None),
        port=getattr(ctx, "_port", None),
    ).revokeGroupMsg(ctx.FromGroupId, ctx.MsgSeq, ctx.MsgRandom)
