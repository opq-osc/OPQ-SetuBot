from PIL import Image, ImageDraw, ImageFont


def text_wrap(font: ImageFont, text, length):
    """
    处理长文本
    :param text: 文本
    :param length: 长度
    :return: 处理完的文本
    """
    # text_list_finally = []
    text_tmp: str = ""
    text_finally: str = ""
    # text_height_finally: int = 0
    for char in text:
        text_tmp += char
        temp_image = Image.new('RGB', (1, 1), (0, 0, 0))
        draw = ImageDraw.Draw(temp_image)
        # text_width, text_height = self.font.getsize(text_tmp)
        text_width = draw.textlength(text_tmp, font=font)
        # print(text_width)
        if text_width > length:
            # print(text_width, pics[i].size[0])
            text_finally += (text_tmp[:-1] if text_finally == "" else text_tmp[1:-1]) + "\n" + text_tmp[-1]
            text_tmp = text_tmp[-1]
    if text_tmp[1:] != "" and text_finally == "":
        text_finally += text_tmp
    elif text_tmp[1:] != "" and text_finally != "":
        text_finally += text_tmp[1:]
    return text_finally
    # return text_list_finally



def get_text_sizes(font: ImageFont, text):
    """
    获取渲染后的文本实际大小
    :param text: 文本
    :return: 渲染后文本的实际size
    """
    # text_size = []
    img = Image.new('RGB', (1, 1), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    size = draw.textbbox((0, 0), text, font=font)
    # print(size)
    return (size[2], size[3])
    # print(self.text_sizes)
    # return text_size


def resize_image(image: Image, max_width, max_height) -> Image.Image:
    # 打开图片

    # 获取原始尺寸
    # 获取原始尺寸
    # 获取原始图像的宽度和高度
    width, height = image.size

    # 计算缩放比例
    scale = min(max_width / width, max_height / height)

    # 计算缩放后的新宽度和新高度
    new_width = int(width * scale)
    new_height = int(height * scale)

    # 缩放图像
    image = image.resize((new_width, new_height))

    # 如果缩放后的图像仍然超过最大尺寸，再次缩放
    if new_width > max_width or new_height > max_height:
        scale = min(max_width / new_width, max_height / new_height)
        new_width = int(new_width * scale)
        new_height = int(new_height * scale)
        image = image.resize((new_width, new_height))

    # 返回缩放后的图像
    return image.convert("RGBA")
