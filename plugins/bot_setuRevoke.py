import random
import re
import time

from botoy import Action, jconfig, GroupMsg
from botoy import decorators as deco

action = Action(qq=jconfig.bot, host=jconfig.host, port=jconfig.port)


@deco.from_botself
def receive_group_msg(ctx: GroupMsg):
    if delay := re.findall(r'REVOKE\[(\d+)]', ctx.Content):
        if delay:
            delay = min(int(delay[0]), 90)
        else:
            delay = random.randint(30, 60)
        time.sleep(delay)
        action.revokeGroupMsg(ctx.QQG, ctx.MsgSeq, ctx.MsgRandom)
