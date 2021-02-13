import random
import json
# import os
from PIL import Image
from pathlib import Path
from module import database
from botoy import decorators as deco
from io import BytesIO
import base64
import re
from module.send import Send as send
from loguru import logger

with open('./config/yuanShenPools/config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())

dicta = {
    'qq': 123,
    'allCount': 12,  # 总次数
    'farFiveStarFloors': 90,  # 离5星保底次数
    'farFourStarFloors': 10,  # 离4星保底次数
    'FiveStarFloorsCount': 0,  # 5星保底数
    'FourStarFloorsCount': 0,  # 4星保底数
    'FiveStarCount': 0,  # 获取到的5星数量
    'FourStarCount': 0,  # 获取到的4星数量
    'certainlyFiveStarUp': False,  # 必定5星up
    'certainlyFourStarUp': False,  # 必定4星up
}


class YuanShen:
    def __init__(self, ctx, count, pool):
        self.ctx = ctx
        self.qq = ctx.QQ
        self.count = count
        self.pool = pool
        self.config = config[pool]
        self.userconf = database.Lottery.getUserInfo(ctx.QQ, config, pool)
        self.articleList = []

    def floors(self, stars: tuple):
        if self.userconf['certainly{}StarUp'.format(stars[0])] and self.config['upArticle'][
            '{}Star'.format(stars[1])] != None:  # UP保底
            # print('上次没有up的保底')
            self.userconf['certainly{}StarUp'.format(stars[0])] = False
            self.articleList.append(random.choice(
                [str(i) for i in Path(self.config['upArticle']['{}Star'.format(stars[1])]).glob('*.png')]))
        elif random.choices([True, False], [self.config['probability']['{}StarUp'.format(stars[1])],
                                            100 - self.config['probability']['{}StarUp'.format(stars[1])]])[
            0] and self.config['upArticle']['{}Star'.format(stars[1])] != None:  # 概率抽UP
            # print('概率的抽到up')
            self.userconf['certainly{}StarUp'.format(stars[0])] = False
            self.articleList.append(random.choice(
                [str(i) for i in Path(self.config['upArticle']['{}Star'.format(stars[1])]).glob('*.png')]))
            # self.articleList.append(random.choice(self.config['upArticle']['{}Star'.format(stars[1])]))

        else:  # 没中UP or 无up的池子
            # print('非up')
            type_pool = random.choices(['role', 'arms'], [self.config['probability']['{}StarRole'.format(stars[1])],
                                                          self.config['probability'][
                                                              '{}StarArms'.format(stars[1])]])[0]
            # print(type_pool)
            if self.config['upArticle']['{}Star'.format(stars[1])] == None:  # 无up的池子
                # print('普通池子')
                if stars[2] == '4':  # 4星都是非限定
                    filePath = '**/*.png'
                elif stars[2] == '5':  # 5星都是限定...普池没有
                    filePath = '*.png'
            else:  # up池
                # print('up池')
                filePath = '*.png'
            res = random.choice(
                [str(i) for i in Path('./config/yuanShenPools/{}_{}'.format(type_pool, stars[2])).rglob(filePath)])
            # print(res)
            self.articleList.append(res)
            self.userconf['certainly{}StarUp'.format(stars[0])] = True

    def draw(self):
        pic = iter(self.articleList)
        # img_x = img.size[0]
        # img_y = img.size[1]
        img_x = 120
        img_y = 120

        interval_x = 50  # x间距
        interval_y = 50  # y间距
        bg_x = 5 * img_x + 6 * interval_x  # 背景x
        bg_y = 2 * img_y + 3 * interval_y  # 背景y
        background = Image.new('RGB', (bg_x, bg_y), (39, 39, 54))
        #
        x1 = 50  # 图像初始x坐标
        y1 = 50  # 图像初始y坐标
        if self.count > 5:
            num_1 = 5
        else:
            num_1 = self.count
        for i in range(num_1):
            background.paste(Image.open(next(pic)), (x1, y1))
            x1 += (img_x + interval_x)
        x1 = 50  # 图像初始x坐标
        if self.count - num_1 > 0:
            for i in range(self.count - num_1):
                background.paste(Image.open(next(pic)), (x1, img_y + 2 * interval_y))
                x1 += (img_x + interval_x)
        # background.show()
        output_buffer = BytesIO()
        background.save(output_buffer, format='JPEG')
        return base64.b64encode(output_buffer.getvalue()).decode()

    def main(self):
        if self.count > 10:
            send.text(self.ctx, '不能>10')
            return
        for i in range(self.count):
            self.userconf['allCount'] += 1
            self.userconf['farFiveStarFloors'] -= 1
            self.userconf['farFourStarFloors'] -= 1

            if self.userconf['farFiveStarFloors'] <= 0:  # 5星保底
                # print('5星保底')
                self.userconf['farFiveStarFloors'] = self.config['fiveStarFloorsCount']
                self.floors(('Five', 'five', '5'))
                continue
            if self.userconf['farFourStarFloors'] <= 0:  # 4星保底
                # print('4星保底')
                self.userconf['farFourStarFloors'] = self.config['fourStarFloorsCount']
                random.choices([lambda: self.floors(('Four', 'four', '4')), lambda: self.floors(('Four', 'four', '4'))],
                               [self.config['fourStarFloorsProbability']['fourStar'],
                                self.config['fourStarFloorsProbability']['fiveStar']])[0]()
                continue
            res = random.choices([5, 4, 3], [
                self.config['probability']['fiveStarRole'] + self.config['probability']['fiveStarArms'],
                self.config['probability']['fourStarRole'] + self.config['probability']['fourStarArms'],
                100 - self.config['probability']['fiveStarRole'] + self.config['probability']['fiveStarArms'] +
                self.config['probability']['fourStarRole'] +
                self.config['probability']['fourStarArms']
            ])[0]
            # print('抽到{}星'.format(res))
            if res == 3:  # 3星
                # self.articleList.append(random.choice(os.listdir('./config/yuanShenPools/arms_3')))
                self.articleList.append(
                    random.choice([str(i) for i in Path('./config/yuanShenPools/arms_3').rglob('*.png')]))
            elif res == 4:
                self.floors(('Four', 'four', '4'))
            else:  # 5星
                self.floors(('Five', 'five', '5'))
        database.Lottery.updateUserinfo(self.qq, self.pool, self.userconf)
        # print(self.userconf)
        # print(self.articleList)
        random.shuffle(self.articleList)
        pic_base64 = self.draw()
        send.picture(self.ctx, '', '', '', False, pic_base64)


@deco.ignore_botself
@deco.with_pattern('原神.*抽')
def receive_group_msg(ctx):
    if info := re.match('原神普池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'permanent').main()
    elif info := re.match('原神角色池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'roleUp').main()
    elif info := re.match('原神武器池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'armsUp').main()


@deco.ignore_botself
@deco.with_pattern('原神.*抽')
def receive_friend_msg(ctx):
    if info := re.match('原神普池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'permanent').main()
    elif info := re.match('原神角色池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'roleUp').main()
    elif info := re.match('原神武器池(\d+)抽', ctx.Content):
        YuanShen(ctx, int(info[1]), 'armsUp').main()
