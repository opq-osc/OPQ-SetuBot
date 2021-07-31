from pydantic import BaseModel


class Probability(BaseModel):
    """基础概率和UP的概率"""
    BaseProbability: float  # 基础概率
    UpProbability: float  # UP概率


class StarLevel(BaseModel):
    """
    获得了指定星级的物品后,具体的武器人物概率
    """
    fiveStar: Probability = Probability(BaseProbability=0.3, UpProbability=0)
    fourStar: Probability = Probability(BaseProbability=2.55, UpProbability=0)


class ItemBaseProbability(BaseModel):
    """
    获得各个星级物品的基础概率
    """
    fiveStarProbability: float = 0.6
    fourStarProbability: float = 5.1


class FloorCount(BaseModel):
    """
    各个星级的保底次数
    """
    fiveStar: int
    fourStar: int


class CardPoolProbability(BaseModel):
    """卡池配置"""
    item: ItemBaseProbability = ItemBaseProbability()
    role: StarLevel = StarLevel()
    arm: StarLevel = StarLevel()
    floorCount: FloorCount = FloorCount(fiveStar=90, fourStar=10)

