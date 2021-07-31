import base64
import random
from io import BytesIO
from pathlib import Path
from typing import List, Union

from PIL import Image
from botoy import FriendMsg, GroupMsg, S

from .database import getUserConfig, updateUserConfig, getPoolItemConfig, getPoolProbabilityConfig
from .model import UserInfo, CardPoolProbability, CardPoolItem

curFileDir = Path(__file__).absolute().parent


class GenshenGacha:
    conversion_dict = {4: 'fourStar', 5: 'fiveStar'}

    def __init__(self, ctx: Union[GroupMsg, FriendMsg], cardPool: str, cardCount: int):
        self.ctx = ctx
        self.send = S.bind(ctx)
        self.cardCount = cardCount
        self.cardPool = cardPool
        self.userConf: UserInfo = getUserConfig(ctx.QQ, cardPool)  # 用户信息
        self.cardPoolProbability: CardPoolProbability = getPoolProbabilityConfig(cardPool)  # 卡池的概率
        self.cardPoolItem: CardPoolItem = getPoolItemConfig(cardPool)  # 卡池中的物品

    def get_item_starLevel(self) -> int:
        """
        :return: 物品的星级,有保底
        """
        self.userConf.fiveStar.notGetCorrespondingCount += 1
        if self.userConf.fiveStar.notGetCorrespondingCount >= self.cardPoolProbability.floorCount.fiveStar:
            self.userConf.fiveStar.notGetCorrespondingCount = 0
            return 5
        self.userConf.fourStar.notGetCorrespondingCount += 1
        if self.userConf.fourStar.notGetCorrespondingCount >= self.cardPoolProbability.floorCount.fourStar:
            self.userConf.fourStar.notGetCorrespondingCount = 0
            return 4
        starLevel = random.choices(
            [5, 4, 3],
            [self.cardPoolProbability.item.fiveStarProbability,
             self.cardPoolProbability.item.fourStarProbability,
             100 - (self.cardPoolProbability.item.fiveStarProbability
                    + self.cardPoolProbability.item.fourStarProbability)]
        )[0]  # 物品星级
        if starLevel == 4:
            self.userConf.fourStar.notGetCorrespondingCount = 0
        elif starLevel == 5:
            self.userConf.fiveStar.notGetCorrespondingCount = 0
        return starLevel

    def extraction_arm_or_role(self, starLevel: int) -> dict:
        """
        根据概率选择武器还是人物
        :param starLevel: 星级
        :return: {'starLevel': 3, 'item': 'role'}
        """
        if starLevel == 3:
            return {'starLevel': 3, 'item': 'role'}

        return random.choices(
            [{'starLevel': starLevel, 'item': 'arm'}, {'starLevel': starLevel, 'item': 'role'}],
            [
                self.cardPoolProbability.arm.dict()[self.conversion_dict[starLevel]]['BaseProbability'],
                self.cardPoolProbability.role.dict()[self.conversion_dict[starLevel]]['BaseProbability']
            ]
        )[0]

    def iffloor(self, item: dict) -> Union[str, None]:
        """
        UP池的保底,up池歪了的话下一次必定是up物品
        :return:
        """
        if self.userConf.dict()[self.conversion_dict[item['starLevel']]]['certainUp']:
            changed_dict = self.userConf.dict()
            changed_dict[self.conversion_dict[item['starLevel']]]['certainUp'] = False  # 复位
            self.userConf = UserInfo(**changed_dict)
            # print('必定UP')
            return random.choice(self.cardPoolItem.dict()[self.conversion_dict[item['starLevel']]]['up'])
        # print('非保底UP')
        return None

    def extraction_specific_items(self, item: dict) -> str:
        """
        根据武器或角色的星级按照概率选择具体物品
        """
        if item['starLevel'] == 3:
            return random.choice(self.cardPoolItem.threeStar)
        if floorItem := self.iffloor(item):
            return floorItem
        specific_item = random.choices(
            [
                random.choice(self.cardPoolItem.dict()[self.conversion_dict[item['starLevel']]]['permanent']),
                random.choice(self.cardPoolItem.dict()[self.conversion_dict[item['starLevel']]]['up'] or ['占位'])
            ],
            [
                self.cardPoolProbability.dict()[item['item']][self.conversion_dict[item['starLevel']]][
                    'BaseProbability'],
                self.cardPoolProbability.dict()[item['item']][self.conversion_dict[item['starLevel']]]['UpProbability']
            ]
        )[0]
        if self.cardPool != 'ordinary' and (
                specific_item not in self.cardPoolItem.dict()[self.conversion_dict[item['starLevel']]]['up']):
            # print('非Up')
            changed_dict = self.userConf.dict()
            changed_dict[self.conversion_dict[item['starLevel']]]['certainUp'] = True  # 在up池出了非UP
            self.userConf = UserInfo(**changed_dict)
        return specific_item

    def draw(self, specific_item: list):
        """
        画图  💩💩💩💩💩💩💩💩💩💩💩
        :return:
        """
        pic = iter([curFileDir / 'icon' / '{}.png'.format(name) for name in specific_item])
        img_x = 130
        img_y = 160

        interval_x = 50  # x间距
        interval_y = 50  # y间距
        bg_x = 5 * img_x + 6 * interval_x  # 背景x
        bg_y = 2 * img_y + 3 * interval_y  # 背景y
        background = Image.new('RGB', (bg_x, bg_y), (39, 39, 54))
        x1 = 50  # 图像初始x坐标
        y1 = 50  # 图像初始y坐标
        if self.cardCount > 5:
            num_1 = 5
        else:
            num_1 = self.cardCount
        for i in range(num_1):
            background.paste(Image.open(next(pic)).resize((img_x, img_y), Image.ANTIALIAS), (x1, y1))
            x1 += (img_x + interval_x)
        x1 = 50  # 图像初始x坐标
        if self.cardCount - num_1 > 0:
            for i in range(self.cardCount - num_1):
                background.paste(Image.open(next(pic)).resize((img_x, img_y), Image.ANTIALIAS),
                                 (x1, img_y + 2 * interval_y))
                x1 += (img_x + interval_x)
        # background.show()
        # output_buffer = BytesIO()
        with BytesIO() as output_buffer:
            background.save(output_buffer, format='JPEG')
            return base64.b64encode(output_buffer.getvalue()).decode()

    def main(self):
        """
        main
        :return:
        """
        if None in [self.userConf, self.cardPoolProbability, self.cardPoolItem]:
            return
        # print('-' * 20)
        # print(self.userConf.dict())
        cards_itemStarLevel: List[int] = [self.get_item_starLevel() for _ in range(self.cardCount)]  # 确定抽的卡都是什么星级的物品
        # print(cards_itemStarLevel)
        items: List[dict] = [self.extraction_arm_or_role(itemStarLevel) for itemStarLevel in cards_itemStarLevel]
        # print(items)
        specific_item = [self.extraction_specific_items(item) for item in items]
        # print(specific_item)
        self.draw(specific_item)
        self.send.image(self.draw(specific_item))
        updateUserConfig(self.ctx.QQ, cardPool=self.cardPool, config=self.userConf)
