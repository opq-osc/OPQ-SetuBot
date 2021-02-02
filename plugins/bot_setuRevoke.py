import random
import re
import time

from botoy import GroupMsg
from botoy import decorators as deco

from module.send import Send as send


@deco.from_botself
def receive_group_msg(ctx: GroupMsg):
    if delay := re.findall(r'REVOKE\[(\d+)]', ctx.Content):
        if delay:
            delay = min(int(delay[0]), 90)
        else:
            delay = random.randint(30, 60)
        time.sleep(delay)
        send.revoke(ctx)
