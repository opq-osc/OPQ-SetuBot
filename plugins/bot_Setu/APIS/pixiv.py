# -*- coding: utf-8 -*-
# @Time    : 2021/6/20 21:01
# @Author  : yuban10703

import hashlib
import json
import random
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import httpx
from botoy import logger, jconfig
from botoy.schedule import scheduler
from tenacity import retry, stop_after_attempt, wait_random

from ._proxies import proxies, async_transport, transport
from ..model import FinishSetuData, GetSetuConfig


class PixivToken:
    def __init__(self):
        self.tokenPath = Path(__file__).parent.parent / ".PixivToken.json"
        self.tokendata = {}
        self.Client = httpx.Client(proxies=proxies, transport=transport)

    def headers(self):
        hash_secret = "28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c"
        X_Client_Time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        X_Client_Hash = hashlib.md5(
            (X_Client_Time + hash_secret).encode("utf-8")
        ).hexdigest()
        headers = {
            "User-Agent": "PixivAndroidApp/5.0.197 (Android 10; Redmi 4)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "zh_CN_#Hans",
            "App-OS": "android",
            "App-OS-Version": "10",
            "App-Version": "5.0.197",
            "X-Client-Time": X_Client_Time,
            "X-Client-Hash": X_Client_Hash,
            "Host": "oauth.secure.pixiv.net",
            "Accept-Encoding": "gzip",
        }
        return headers

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2))
    def do_refresh_token(self):
        logger.info("尝试刷新Pixiv_token")
        url = "https://oauth.secure.pixiv.net/auth/token"
        data = {
            "client_id": "MOBrBDS8blbauoSck0ZfDbtuzpyT",
            "client_secret": "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj",
            "grant_type": "refresh_token",
            "refresh_token": jconfig.get_configuration().get("setu.refresh_token"),
            "device_token": self.tokendata["device_token"]
            if "device_token" in self.tokendata.keys()
            else uuid.uuid4().hex,
            "get_secure_url": "true",
            "include_policy": "true",
        }
        self.tokendata = self.Client.post(url, data=data, headers=self.headers()).json()
        self.tokendata["time"] = time.time()
        logger.success("刷新token成功~")
        self.saveToken()

    def continue_refresh_token(self):
        try:
            self.do_refresh_token()
        except Exception as e:
            logger.error(f"刷新失败\r\n{e}")
            nextTime = 300
        else:
            nextTime = int(
                self.tokendata["expires_in"] - (time.time() - self.tokendata["time"])
            )
        self.addJob(nextTime)
        return

    def saveToken(self):
        with open(self.tokenPath, "w", encoding="utf-8") as f:
            json.dump(self.tokendata, f, indent=4, ensure_ascii=False)
        jconfig.get_configuration("setu").update("refresh_token", self.tokendata["refresh_token"])
        logger.success("PixivToken已保存到.PixivToken.json")
        return

    def addJob(self, next_time: int):
        logger.info("离下次刷新还有:{}s".format(next_time))
        utc_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        scheduler.add_job(
            self.continue_refresh_token,
            next_run_time=beijing_time + timedelta(seconds=next_time - 1),
            misfire_grace_time=30,
        )

    def main(self):
        try:
            with open(self.tokenPath, "r", encoding="utf-8") as f:
                self.tokendata = json.load(f)
                logger.success("读取.PixivToken.json成功~")
        except Exception as e:
            logger.error(".PixivToken.json载入失败,请检查内容并重新启动~\r\n{}".format(e))
            sys.exit(0)
        if jconfig.get_configuration().get("setu.refresh_token") == "":
            logger.error("PixivToken不存在")
            sys.exit(0)
        if "time" not in self.tokendata.keys():  # 没time字段就是第一次启动
            self.continue_refresh_token()
            return
        if time.time() - self.tokendata["time"] >= int(
                self.tokendata["expires_in"]
        ):  # 停止程序后再次启动时间后的间隔时间超过刷新间隔
            self.continue_refresh_token()
            return
        self.addJob(
            int(self.tokendata["expires_in"] - (time.time() - self.tokendata["time"]))
        )


pixivToken = PixivToken()
pixivToken.main()


class Pixiv:
    def __init__(self, config: GetSetuConfig):
        self.config = config

    async def get(self):  # p站热度榜
        tags = self.config.tags.copy()
        if self.config.level == 1:  # R18 only
            tags.append("R-18")
        elif self.config.level == 2:  # all
            if random.choice([True, False]):
                tags.append("R-18")
        url = "https://app-api.pixiv.net/v1/search/popular-preview/illust"
        params = {
            "filter": "for_android",
            "include_translated_tag_results": "true",
            "merge_plain_keyword_results": "true",
            "word": " ".join(tags),
            "search_target": "partial_match_for_tags",
        }  # 精确:exact_match_for_tags,部分:partial_match_for_tags
        headers = pixivToken.headers()
        headers["Host"] = "app-api.pixiv.net"
        headers["Authorization"] = "Bearer {}".format(
            pixivToken.tokendata["access_token"]
        )
        try:
            async with httpx.AsyncClient(
                    proxies=proxies, transport=async_transport
            ) as client:
                res = await client.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
        except Exception as e:
            logger.warning("Pixiv热度榜获取失败~:\r\n{}".format(e))
            return []
        else:
            if res.status_code == 200:
                data_finally = self.process_data(data)
                if len(data_finally) <= self.config.toGetNum - self.config.doneNum:
                    return data_finally
                else:
                    return random.sample(
                        self.process_data(data),
                        self.config.toGetNum - self.config.doneNum,
                    )
            else:
                logger.warning("Pixiv热度榜异常:{}\r\n{}".format(res.status_code, data))
                return []

    def buildOriginalUrl(self, original_url: str, page: int) -> str:
        def changePage(matched):
            if page > 1:
                return "-%s" % (int(matched[0][-1]) + 1)
            else:
                return ""

        msg_changeHost = re.sub(r"//.*/", r"//pixiv.re/", original_url)
        return re.sub(r"_p\d+", changePage, msg_changeHost)

    def process_data(self, data) -> List[FinishSetuData]:
        dataList = []
        for d in data["illusts"]:
            if d["x_restrict"] == 2:  # R18G
                continue
            if self.config.level == 0 and d["x_restrict"] == 1:  # 未开启R18
                continue
            if d["page_count"] != 1:  # 多页画廊
                OriginalUrl = d["meta_pages"][0]["image_urls"]["original"]
            else:
                OriginalUrl = d["meta_single_page"]["original_image_url"]
            dataList.append(
                FinishSetuData(
                    title=d["title"],
                    picID=d["id"],
                    picWebUrl="www.pixiv.net/artworks/" + str(d["id"]),
                    page="0",
                    author=d["user"]["name"],
                    authorID=d["user"]["id"],
                    authorWebUrl="www.pixiv.net/users/" + str(d["user"]["id"]),
                    picOriginalUrl=OriginalUrl,
                    picLargeUrl=d["image_urls"]["large"].replace("_webp", ""),
                    picMediumUrl=d["image_urls"]["medium"].replace("_webp", ""),
                    picOriginalUrl_Msg=self.buildOriginalUrl(
                        OriginalUrl, d["page_count"]
                    ),
                    tags=",".join([i["name"] for i in d["tags"]]),
                )
            )
        return dataList

    async def main(self) -> List[FinishSetuData]:
        if self.config.toGetNum - self.config.doneNum <= 0:
            return []
        if len(self.config.tags) == 0:
            return []
        return await self.get()
