from typing import List

import httpx
from loguru import logger

from ..model import FinishSetuData, GetSetuConfig
from ._proxies import proxies, transport


class Yuban:
    def __init__(self, config: GetSetuConfig):
        self.config = config

    def get(self) -> List[FinishSetuData]:
        try:
            with httpx.Client(proxies=proxies, transport=transport) as client:
                res = client.get(
                    url="http://api.yuban10703.xyz:2333/setu_v4",
                    params={
                        "level": self.config.level + 1,
                        "num": self.config.toGetNum - self.config.doneNum,
                        "tag": self.config.tags,
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
                        title=d["title"],
                        picID=d["artwork"],
                        picWebUrl="www.pixiv.net/artworks/" + str(d["artwork"]),
                        page=d["page"],
                        author=d["author"],
                        authorID=d["artist"],
                        authorWebUrl="www.pixiv.net/users/" + str(d["artist"]),
                        picOriginalUrl=d["original"],
                        picLargeUrl=d["large"].replace("_webp", ""),
                        picMediumUrl=d["medium"].replace("_webp", ""),
                        picOriginalUrl_Msg=d["original"].replace(
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
