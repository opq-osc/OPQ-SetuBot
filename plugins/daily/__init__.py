import asyncio
import re
from typing import Union
from datetime import date
import httpx
from PIL import Image, ImageDraw, ImageFont
from .draw import singlePage, merge_pages, add_logo_and_info
import json
from pathlib import Path

from botoy import S, ctx, mark_recv, logger, contrib, Action, jconfig

curFileDir = Path(__file__).parent  # 当前文件路径


@contrib.to_async
def get_bangumi_config(weekday):
    path = curFileDir / "config" / "bangumi.json"  # 拼接路径
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data[str(weekday)]
    except Exception as e:
        logger.error("请检查bangumi.json")
        return None


async def main():
    if m := (ctx.group_msg or ctx.friend_msg):
        if m.text == "今日番剧":
            today = date.today()
            weekday = today.weekday() + 1
            data = await get_bangumi_config(weekday)
            # print(data)
            p = []
            iter_data = iter(data)
            next(iter_data)
            for k, v in data.items():
                pics = []
                names = []
                tags = []
                for fanju in v:
                    pics.append(Image.open(str(curFileDir / "files" / "bangumi" / fanju["filename"])))
                    names.append(fanju["name"])
                    tags.append(fanju["tags"])
                next_time = next(iter_data, None)
                # print(k, next_time)
                p.append(singlePage(pics, names, tags, k, next_time))
            img = add_logo_and_info(merge_pages(p))

            await S.image(img)


mark_recv(main, author='yuban10703', name="今日番剧", usage='发送"今日番剧"')
