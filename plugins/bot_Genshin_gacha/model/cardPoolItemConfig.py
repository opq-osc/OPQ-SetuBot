from pydantic import BaseModel


class Item(BaseModel):
    up: list = []
    permanent: list = []


class CardPoolItem(BaseModel):
    fiveStar: Item = Item()
    fourStar: Item = Item()
    threeStar: list = []
