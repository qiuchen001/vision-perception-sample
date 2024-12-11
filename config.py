import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 服务器配置
    SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '30501'))

    # 视频处理配置
    VIDEO_FRAME_INTERVAL = int(os.getenv('VIDEO_FRAME_INTERVAL', '30'))  # 视频抽帧间隔
    VIDEO_FRAME_BATCH_SIZE = int(os.getenv('VIDEO_FRAME_BATCH_SIZE', '50'))  # 批处理大小

    # ... 其他配置 ...