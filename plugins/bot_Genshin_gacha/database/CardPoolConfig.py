from pathlib import Path
from typing import Union

import ujson as json
from loguru import logger

from ..model import CardPoolItem, CardPoolProbability

configDir = Path(__file__).absolute().parent.parent / 'config'


def getPoolProbabilityConfig(cardPool: str) -> Union[CardPoolProbability, None]:
    try:
        with open(configDir / 'cardPoolProbability.json', "r", encoding="utf-8") as f:
            data = json.load(f)
        return CardPoolProbability(**data[cardPool])
    except Exception as e:
        logger.error("请检查cardPoolProbability.json\r\n{}".format(e))
        return None


def getPoolItemConfig(cardPool: str) -> Union[CardPoolItem, None]:
    try:
        with open(configDir / 'cardPoolItem.json', "r", encoding="utf-8") as f:
            data = json.load(f)
        return CardPoolItem(**data[cardPool])
    except Exception as e:
        logger.error("请检查cardPoolItem.json\r\n{}".format(e))
        return None
