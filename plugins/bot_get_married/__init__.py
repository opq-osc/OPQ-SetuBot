from io import BytesIO
from pathlib import Path
from typing import Union

from botoy import FriendMsg, GroupMsg, MsgTypes, S
from botoy import async_decorators as deco
from botoy.contrib import to_async
from httpx import AsyncClient
from PIL import Image

curFileDir = Path(__file__).parent  # 当前文件路径


@to_async
def build_img(pic_bytes: BytesIO) -> BytesIO:
    head_portrait = Image.open(pic_bytes)
    template = Image.open(str(curFileDir / "template.png"))
    template.thumbnail((head_portrait.size[0], head_portrait.size[1]))
    head_portrait.paste(template, (0, 0), mask=template)
    bf = BytesIO()
    head_portrait.save(bf, format="JPEG", quality=90)
    return bf


async def download_head_portrait(qq: int) -> BytesIO:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"
    async with AsyncClient() as client:
        data = await client.get(url)
    return BytesIO(data.content)


@deco.ignore_botself
@deco.these_msgtypes(MsgTypes.TextMsg)
@deco.startswith("结婚")
async def main(ctx: Union[GroupMsg, FriendMsg]):
    qq_id = ctx.Content[2:].strip()
    if qq_id.isspace() or len(qq_id) == 0:
        await S.atext("要和谁结婚捏?")
        return
    if not qq_id.isdigit():
        await S.atext("只能QQ号哦")
        return
    head_portrait = await download_head_portrait(int(qq_id))
    img = await build_img(head_portrait)
    await S.aimage(img)


receive_group_msg = receive_friend_msg = main
