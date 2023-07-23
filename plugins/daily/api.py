import httpx
from botoy import logger
import asyncio

async def get_bangumi():
    url = "https://api.bgm.tv/calendar"
    headers = {
        "Referer": "https://t.bilibili.com/",
        "User-Agent": "opq-osc/OPQ-SetuBot (https://github.com/opq-osc/OPQ-SetuBot)"
    }
    async with httpx.AsyncClient() as c:
        res = await c.get(url, headers=headers)
        data = res.json()
        print(data)
        return data

async def get_bili_():
    url = "https://app.bilibili.com/x/topic/web/dynamic/rcmd?source=Web&page_size=9"
    headers = {
        "Referer": "https://t.bilibili.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36 Edg/114.0.1823.82"

    }
    async with httpx.AsyncClient() as c:
        res = await c.get(url, headers=headers)
        data = res.json()
        print(data)
        return data


async def get_60s():
    url = "https://api.emoao.com/api/60s"
    params = {
        "type": "json"
    }
    async with httpx.AsyncClient() as c:
        res = await c.get(url, params=params)
        data = res.json()
        print(data)
        return data

asyncio.run(get_bangumi())