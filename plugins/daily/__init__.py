import json
import re
from datetime import date
from pathlib import Path

from botoy import S, ctx, mark_recv, logger, contrib

from .draw import build_bangumi_image

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


prefixes = ["番剧", "番剧列表"]
pattern = r'\b(?:' + '|'.join(prefixes) + r')\s*(\d+)\b'


async def main():
    if m := (ctx.group_msg or ctx.friend_msg):
        if m.text in ["今日番剧", "番剧", "番剧列表"]:
            weekday = date.today().weekday() + 1
            # print(weekday)
            data = await get_bangumi_config(weekday)
            await S.image(await build_bangumi_image(data, weekday))
        elif m.text in ["明日番剧"]:
            weekday = date.today().weekday() + 1
            if weekday == 7:
                weekday = 1
            else:
                weekday += 1
            data = await get_bangumi_config(weekday)
            await S.image(await build_bangumi_image(data, weekday))
        elif m.text in ["昨日番剧"]:
            weekday = date.today().weekday() + 1
            if weekday == 1:
                weekday = 7
            else:
                weekday -= 1
            data = await get_bangumi_config(weekday)
            await S.image(await build_bangumi_image(data, weekday))
        elif info := re.findall(pattern, m.text):
            if info[0].isdigit():
                weekday = int(info[0])
                # print(weekday)
                if 1 <= weekday <= 7:
                    data = await get_bangumi_config(weekday)
                    await S.image(await build_bangumi_image(data, weekday))
                else:
                    await S.text("?")
            else:
                await S.text("要阿拉伯数字哦")


mark_recv(main, author='yuban10703', name="今日番剧", usage='发送"今日番剧"')
