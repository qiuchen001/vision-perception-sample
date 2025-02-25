import math
from PIL import Image


def smart_resize(
        image_path, factor=28, vl_high_resolution_images=False):
    """
    对图像进行预处理。

    参数:
        image_path：图像的路径
        factor：图像转换为Token的最小单位
        vl_high_resolution_images：是否提高模型的单图Token上限

    """
    # 打开指定的PNG图片文件
    image = Image.open(image_path)

    # 获取图片的原始尺寸
    height = image.height
    width = image.width
    # 将高度调整为28的整数倍
    h_bar = round(height / factor) * factor
    # 将宽度调整为28的整数倍
    w_bar = round(width / factor) * factor

    # 图像的Token下限：4个Token
    min_pixels = 28 * 28 * 4

    # 根据vl_high_resolution_images参数确定图像的Token上限
    if not vl_high_resolution_images:
        max_pixels = 1280 * 28 * 28
    else:
        max_pixels = 16384 * 28 * 28

    # 对图像进行缩放处理，调整像素的总数在范围[min_pixels,max_pixels]内
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = math.floor(height / beta / factor) * factor
        w_bar = math.floor(width / beta / factor) * factor
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = math.ceil(height * beta / factor) * factor
        w_bar = math.ceil(width * beta / factor) * factor
    return h_bar, w_bar


# 将xxx/test.png替换为你本地的图像路径
h_bar, w_bar = smart_resize("./这是一条城市街道，有汽车、人行横道、行人和红色交通灯.jpg")
print(f"缩放后的图像尺寸为：高度为{h_bar}，宽度为{w_bar}")

# 计算图像的Token数：总像素除以28 * 28
token = int((h_bar * w_bar) / (28 * 28))

# <|vision_bos|> 和 <|vision_eos|> 作为视觉标记，每个需计入 1个Token
print(f"图像的总Token数为{token + 2}")