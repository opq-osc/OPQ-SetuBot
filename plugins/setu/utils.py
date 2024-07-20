import time
from io import BytesIO
from typing import Union

from botoy import jconfig, logger
from PIL import Image
from tenacity import AsyncRetrying, stop_after_attempt, wait_random


setu_config = jconfig.get_configuration("setu")


def transpose_setu(setu: bytes) -> bytes:
    logger.info("翻转图片")
    raw = Image.open(BytesIO(setu))
    with BytesIO() as bf:
        raw.transpose(3).save(bf, format="png")
        return bf.getvalue()


async def download_setu(client, url) -> Union[bytes, str]:
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2)):
        with attempt:
            try:
                res = await client.get(url)
                if res.status_code != 200:
                    logger.warning("download_setu: res.status_code != 200")
                    raise Exception("download_setu: res.status_code != 200")
                with BytesIO() as bf:
                    bf.write(res.content)
                    if setu_config.get("transpose"):
                        return transpose_setu(bf.getvalue())
                    bf.write(str(time.time()).encode("utf-8"))  # 增加信息,改变MD5
                    return bf.getvalue()
            except Exception as e:
                logger.error(f"Attempt failed: {e}")
                raise  # Reraise exception to trigger retry

    return "https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/error.jpg"
