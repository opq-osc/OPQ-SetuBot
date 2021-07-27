# -*- coding: utf-8 -*-
# @Time    : 2021/6/20 21:01
# @Author  : yuban10703

from typing import List

import httpx
from loguru import logger

from ..model import FinishSetuData, GetSetuConfig
from ._proxies import proxies, transport


class Lolicon:
    def __init__(self, config: GetSetuConfig):
        self.config = config

    def get(self) -> List[FinishSetuData]:
        try:
            # with httpx.Client() as client:
            with httpx.Client(proxies=proxies, transport=transport) as client:
                res = client.post(
                    url="https://api.lolicon.app/setu/v2",
                    json={
                        "r18": self.config.level,
                        "num": self.config.toGetNum - self.config.doneNum,
                        "tag": self.config.tags,
                        "size": ["original", "regular", "small"],
                        "proxy": False,
                    },
                    timeout=8,
                )
        except Exception as e:
            logger.warning("Lolicon:\r\n{}".format(e))
            return []
        if res.status_code == 200:
            dataList = []
            datas = res.json()["data"]
            for d in datas:
                dataList.append(
                    FinishSetuData(
                        title=d["title"],
                        picID=d["pid"],
                        picWebUrl="www.pixiv.net/artworks/" + str(d["pid"]),
                        page=d["p"],
                        author=d["author"],
                        authorID=d["uid"],
                        authorWebUrl="www.pixiv.net/users/" + str(d["uid"]),
                        picOriginalUrl=d["urls"]["original"],
                        picLargeUrl=d["urls"]["regular"],
                        picMediumUrl=d["urls"]["small"],
                        picOriginalUrl_Msg=d["urls"]["original"].replace(
                            "i.pximg.net", "i.pixiv.cat"
                        ),
                        # tags=self.config.tags,
                        tags=",".join(d["tags"]),
                    )
                )
            return dataList
        return []

    def main(self) -> List[FinishSetuData]:
        if self.config.toGetNum - self.config.doneNum <= 0:
            return []
        return self.get()
