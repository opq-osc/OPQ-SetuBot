import base64
import json
import re
from datetime import date
from pathlib import Path

from botoy import S, ctx, mark_recv, logger, contrib, async_scheduler, jconfig, Action
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_fixed

from .draw import build_bangumi_image, build_specified_bangumi_image

curFileDir = Path(__file__).parent  # 当前文件路径


@contrib.to_async
def get_bangumi_config(weekday=None):
    path = curFileDir / "config" / "bangumi.json"  # 拼接路径
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if weekday:
            return data[str(weekday)]
        return data
    except Exception as e:
        logger.error(e)
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
            print(data)
            # await build_specified_bangumi_image(data["01:50"],weekday,"01:05")
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


async def push_bangumi(data: list, weekday: int, update_time):
    whitelist = jconfig.get("bangumi_push_whitelist")
    blacklist = jconfig.get("bangumi_push_blacklist")
    # print(whitelist)
    # print(blacklist)
    pic = await build_specified_bangumi_image(data, weekday, update_time)
    action = Action(qq=jconfig["qq"], url=jconfig["url"])
    try:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(2)):
            with attempt:
                groupList = await action.getGroupList()
    except RetryError:
        logger.error(f"番剧更新推送:获取群数据失败")
        return
    # print(groupList)
    groupid_list_mark = []
    if whitelist == []:
        for group in groupList:
            groupid = group["GroupCode"]
            if groupid in blacklist:
                continue
            groupid_list_mark.append(groupid)
    else:
        groupid_list_mark = whitelist
    for groupid in groupid_list_mark:
        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(2)):
                with attempt:
                    await action.sendGroupPic(groupid, base64=base64.b64encode(pic).decode())
        except RetryError:
            logger.error(f"番剧更新推送[{groupid}]发送失败")


async def add_scheduler_job():
    # weekday = date.today().weekday() + 1
    # print(weekday)
    data: dict = await get_bangumi_config()
    for day, day_data in data.items():
        for update_time, bangumi_data in day_data.items():
            hour, minute = update_time.split(":")
            # print(day, hour, minute)
            async_scheduler.add_job(
                push_bangumi,
                "cron",
                args=[bangumi_data, int(day), update_time],
                day_of_week=int(day) - 1,
                hour=int(hour),
                minute=int(minute),
                misfire_grace_time=30,
            )


if jconfig.get("bangumi_push"):
    logger.warning("已开启番剧推送")
    contrib.sync_run(add_scheduler_job())

mark_recv(main, author='yuban10703', name="今日番剧", usage='发送"今日番剧"')
