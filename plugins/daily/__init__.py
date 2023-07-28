import asyncio
import re
import time
from typing import Union
from datetime import date
import httpx
from PIL import Image, ImageDraw, ImageFont
from .draw import build_today_bangumi_image
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
            await S.image(await build_today_bangumi_image(data))


mark_recv(main, author='yuban10703', name="今日番剧", usage='发送"今日番剧"')
