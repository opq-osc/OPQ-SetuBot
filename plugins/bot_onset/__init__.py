from pathlib import Path
from botoy import MsgTypes, S, GroupMsg, FriendMsg
import random
from typing import Union
import ujson as json
from botoy import async_decorators as deco

curFileDir = Path(__file__).parent  # 当前文件路径

with open(curFileDir / "onset.json", "r", encoding="utf-8") as f:
    data: list = json.load(f)["data"]


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.TextMsg)
@deco.startswith("发病")
async def main(ctx: Union[GroupMsg, FriendMsg]):
    name = ctx.Content[2:].strip()
    if name.isspace() or len(name) == 0:
        S.text("要对谁发病捏?")
        return
    content: str = random.choice(data)["content"]
    S.text(content.replace("{{user.name}}", name))


receive_group_msg = receive_friend_msg = main
