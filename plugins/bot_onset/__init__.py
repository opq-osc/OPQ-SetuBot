import random
from pathlib import Path
from typing import Union

import ujson as json
from botoy import FriendMsg, GroupMsg, MsgTypes, S
from botoy import async_decorators as deco

curFileDir = Path(__file__).parent  # 当前文件路径

with open(curFileDir / "onset.json", "r", encoding="utf-8") as f:
    data: list = json.load(f)["data"]


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.TextMsg)
@deco.startswith("发病")
async def main(ctx: Union[GroupMsg, FriendMsg]):
    name = ctx.Content[2:].strip()
    if name.isspace() or len(name) == 0 or "[ATALL()]" in name:
        await S.atext("要对谁发病捏?")
        return
    content: str = random.choice(data)["content"]
    await S.atext(content.replace("{{user.name}}", name))


receive_group_msg = receive_friend_msg = main
