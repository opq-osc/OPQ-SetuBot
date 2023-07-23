from .utils import resize_image, text_wrap, get_text_sizes
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
import base64
import random

import datetime

curFileDir = Path(__file__).parent  # 当前文件路径

background_color = (255, 255, 255)


def singlePage(pics, titles, tags, update_time, next_time):
    pics_fin = []
    border_color = (255, 255, 255)  # 白色边框
    border_width = 2
    for pic in pics:
        pics_fin.append(ImageOps.expand(resize_image(pic, 300, 400), border=border_width, fill=border_color))
    background_size_x = 1100
    background_size_y = 0
    gap_y = 40
    for pic in pics_fin:
        background_size_y += gap_y + pic.size[1]
    ###################
    background = Image.new("RGB", (background_size_x, background_size_y), background_color)
    draw = ImageDraw.Draw(background)
    update_time_coordinate = (100, 0)

    update_time_font = ImageFont.truetype(str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf"), 38)
    draw.text(update_time_coordinate, update_time, font=update_time_font,
              fill=(173, 173, 173))
    ###################
    pic_coordinate_x = 215
    pic_coordinate_y = 0
    ###################
    title_font = ImageFont.truetype(str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf"), 45)
    title_coordinate_x = 535
    title_coordinate_y = 0
    ###################
    tags_font = ImageFont.truetype(str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf"), 40)
    tags_coordinate_x = title_coordinate_x
    tags_coordinate_y = 0
    for i in range(len(pics)):
        background.paste(pics_fin[i], (pic_coordinate_x, pic_coordinate_y))
        pic_coordinate_y += gap_y + pics_fin[i].size[1]
        ###################
        draw.text((title_coordinate_x, title_coordinate_y), text_wrap(title_font, titles[i], 500), font=title_font,
                  fill=(34, 34, 34))
        title_coordinate_y += gap_y + pics_fin[i].size[1]
        ###################
        tags_text = text_wrap(tags_font, ",".join(tags[i]), 500)
        tag_x, tag_y = get_text_sizes(tags_font, tags_text)
        # print(tag_x, tag_y)
        tags_coordinate_y += pics_fin[i].size[1] if i == 0 else pics_fin[i].size[1] + gap_y
        draw.text((tags_coordinate_x, tags_coordinate_y - tag_y), tags_text, font=tags_font, fill=(251, 114, 153))
    ###############
    start_point = (75, 44)
    end_point = (start_point[0], background_size_y)
    draw.line([start_point, end_point], width=3, fill=(251, 114, 153))
    ###############
    center = (start_point[0], 21)
    radius = 9
    circle_color = (251, 114, 153)
    draw.ellipse([(center[0] - radius, center[1] - radius),
                  (center[0] + radius, center[1] + radius)],
                 outline=circle_color, fill=circle_color)
    ###############
    time_format = "%H:%M"

    current_time = datetime.datetime.now().time()
    start_time = datetime.datetime.strptime(update_time, time_format).time()
    if next_time:
        end_time = datetime.datetime.strptime(next_time, time_format).time()
    else:
        end_time = datetime.datetime.strptime("00:00", time_format).time()
    if start_time <= current_time <= end_time:
        total_minutes = (end_time.hour - start_time.hour) * 60 + (end_time.minute - start_time.minute)
        elapsed_minutes = (current_time.hour - start_time.hour) * 60 + (current_time.minute - start_time.minute)
        percentage = max(0.07, min(0.93, (elapsed_minutes / total_minutes)))
        # print(percentage)
        length = end_point[1] - start_point[1]
        position_ratio = percentage * length
        position = start_point[1] + position_ratio
        # print(position)
        draw.ellipse([(center[0] - radius, position - radius),
                      (center[0] + radius, position + radius)],
                     outline=circle_color, fill=circle_color)
        formatted_time = datetime.datetime.now().strftime("%#H:%M")
        draw.text((100, position - 45), f"now\n{formatted_time}", font=update_time_font,
                  fill=(251, 114, 153))
    # background.show()

    return background


def merge_pages(pages):
    background_size_X = 1100
    background_size_Y = 10
    page_coordinates = []
    gap_Y = 0
    for i in range(len(pages)):
        if i == 0:
            page_coordinates.append((0, 230))
            # background.paste(pages[i], (0, gap_Y))
            background_size_Y += (230 + pages[i].size[1])

        else:
            # print(i)
            page_coordinates.append((0, gap_Y + page_coordinates[i - 1][1] + pages[i - 1].size[1]))
            # background.paste(pages[i], (0, gap_Y + page_coordinates[i - 1][1] + pages[i - 1].size[1]))
            background_size_Y += (gap_Y + pages[i].size[1])
    # print(background_size_Y)
    background = Image.new("RGB", (background_size_X, background_size_Y), background_color)
    for i in range(len(pages)):
        background.paste(pages[i], page_coordinates[i])
    # title_font = ImageFont.truetype(str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf"), 80)
    # title = "番剧时间表"
    # text_width, text_height = get_text_sizes(title_font, title)
    # text_x = (background_size_X - text_width) // 2
    # text_y = 30
    # draw = ImageDraw.Draw(background)
    # # draw.text((text_x, text_y), title, font=title_font, fill=(0, 0, 0))
    # target_image = Image.open(str(curFileDir.parent / "files" / "bangumi" / "icons" / "icons_03.png"))
    # paste_position = (70, 70)  # 在目标图像上的坐标位置
    #
    # # 粘贴源图像到目标图像上
    # background.paste(target_image, paste_position, mask=target_image)
    # #
    # draw = ImageDraw.Draw(background)
    # start_point = (80, 200)
    # end_point = (260, 200)
    #
    # draw.line([start_point, end_point], width=20, fill=(251, 114, 153))
    # background.show()
    return background


def add_logo_and_info(pic):
    current_date = datetime.datetime.now().strftime("%m-%d")
    today = datetime.datetime.now()
    weekday = today.weekday()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_name = weekday_names[weekday]
    target_image = Image.open(
        str(curFileDir.parent / "files" / "bangumi" / "icons" / f"{random.randint(1, 5)}.png")).resize((190, 190))
    paste_position = (20, 0)  # 在目标图像上的坐标位置

    # 粘贴源图像到目标图像上
    pic.paste(target_image, paste_position, mask=target_image)
    #
    draw = ImageDraw.Draw(pic)
    start_point = (60, 200)
    end_point = (400, 200)

    draw.line([start_point, end_point], width=20, fill=(251, 114, 153))
    #
    current_date_font = ImageFont.truetype(str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf"), 60)
    # text_width, text_height = get_text_sizes(title_font, title)
    text_x = 220
    text_y = 60
    draw.text((text_x, text_y), current_date, font=current_date_font, fill=(0, 0, 0))
    draw.text((text_x, 120), weekday_name, font=current_date_font, fill=(0, 0, 0))
    # pic.show()
    with BytesIO() as bf:
        pic.save(bf, format="JPEG", quality=80)
        return bf.getvalue()
