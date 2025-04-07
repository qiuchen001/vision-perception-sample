import cv2
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


def extract_frames(video_path, frame_interval=1):
    """
    从视频中提取帧。

    参数:
        video_path：视频文件路径
        frame_interval：帧提取的时间间隔（秒）

    返回:
        frames：提取的帧列表
    """
    frames = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频帧率
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数
    interval_frames = int(frame_interval * fps)  # 转换为帧间隔

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % interval_frames == 0:  # 按间隔提取帧
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 转换为 RGB 格式
            pil_image = Image.fromarray(frame_rgb)  # 转换为 PIL 图像
            frames.append(pil_image)
        frame_count += 1

    cap.release()
    return frames


def calculate_video_tokens(video_path, frame_interval=1, factor=28, vl_high_resolution_images=False):
    """
    计算视频所需消耗的 Token 数。

    参数:
        video_path：视频文件路径
        frame_interval：帧提取的时间间隔（秒）
        factor：图像转换为 Token 的最小单位
        vl_high_resolution_images：是否提高模型的单图 Token 上限

    返回:
        total_tokens：视频所需的总 Token 数
    """
    # 提取视频帧
    frames = extract_frames(video_path, frame_interval)

    total_tokens = 0
    for frame in frames:
        # 将 PIL 图像保存为临时文件并调用 smart_resize
        temp_image_path = "temp_frame.png"
        frame.save(temp_image_path)
        h_bar, w_bar = smart_resize(temp_image_path, factor=factor, vl_high_resolution_images=vl_high_resolution_images)

        # 计算单帧 Token 数
        token_per_frame = int((h_bar * w_bar) / (factor * factor))
        total_tokens += token_per_frame + 2  # 加上 <|vision_bos|> 和 <|vision_eos|>

    return total_tokens


# 示例：计算视频的 Token 消耗
video_path = "./example_video.mp4"  # 替换为你的视频路径
frame_interval = 1  # 每秒提取一帧
total_tokens = calculate_video_tokens(video_path, frame_interval=frame_interval, vl_high_resolution_images=True)
print(f"视频的总 Token 数为：{total_tokens}")