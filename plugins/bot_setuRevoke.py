import asyncio
import random
import re

from botoy import AsyncAction, GroupMsg
from botoy.async_decorators import from_botself


@from_botself
async def main(ctx: GroupMsg):
    if "REVOKE" not in ctx.Content:
        return
    if delay := re.findall(r"REVOKE\[(\d+)]", ctx.Content):
        delay = min(int(delay[0]), 90)
    else:
        delay = random.randint(30, 60)

    await asyncio.sleep(delay)

    async with AsyncAction.from_ctx(ctx) as action:
        await action.revokeGroupMsg(ctx.QQG, ctx.MsgSeq, ctx.MsgRandom)


async def receive_group_msg(ctx: GroupMsg):
    await main(ctx)
