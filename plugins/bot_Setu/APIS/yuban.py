from typing import List

import httpx
from botoy import logger

from ..model import FinishSetuData, GetSetuConfig


class Yuban:
    def __init__(self, config: GetSetuConfig):
        self.config = config

    async def get(self) -> List[FinishSetuData]:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    url="https://setu.yuban10703.xyz/setu",
                    params={
                        "r18": self.config.level,
                        "num": self.config.toGetNum - self.config.doneNum,
                        "tags": self.config.tags,
                    },
                    timeout=8,
                )
        except Exception as e:
            logger.warning("YubanAPI:\r\n{}".format(e))
            return []
        if res.status_code == 200:
            dataList = []
            datas = res.json()["data"]
            for d in datas:
                dataList.append(
                    FinishSetuData(
                        title=d["artwork"]["title"],
                        picID=d["artwork"]["id"],
                        picWebUrl="www.pixiv.net/artworks/" + str(d["artwork"]["id"]),
                        page=d["page"],
                        author=d["author"]["name"],
                        authorID=d["author"]["id"],
                        authorWebUrl="www.pixiv.net/users/" + str(d["author"]["id"]),
                        picOriginalUrl=d["urls"]["original"],
                        picLargeUrl=d["urls"]["large"].replace("_webp", ""),
                        picMediumUrl=d["urls"]["medium"].replace("_webp", ""),
                        picOriginalUrl_Msg=d["urls"]["original"].replace(
                            "i.pximg.net", "i.pixiv.re"
                        ),
                        # tags=self.config.tags,
                        tags=",".join(d["tags"]),
                    )
                )
            return dataList
        return []

    async def main(self) -> List[FinishSetuData]:
        if self.config.toGetNum - self.config.doneNum <= 0:
            return []
        return await self.get()
