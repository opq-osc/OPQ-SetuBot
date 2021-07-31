from pydantic import BaseModel


class StarLevelInfo(BaseModel):
    getCount: int = 0  # 总共抽到多少
    notGetCorrespondingCount: int = 0  # 没获取到对应星级的次数,抽到对应星级就归零
    certainUp: bool = False  # 必定UP


class UserInfo(BaseModel):
    """
    用户信息
    """
    userid: int
    fiveStar: StarLevelInfo = StarLevelInfo()
    fourStar: StarLevelInfo = StarLevelInfo()
