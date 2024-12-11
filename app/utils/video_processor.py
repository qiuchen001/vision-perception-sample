import cv2
import base64
import numpy as np
from typing import List


class VideoProcessor:
    def extract_key_frames(self, video_url: str, interval_sec: float = 1.0) -> List[str]:
        """提取视频关键帧
        Args:
            video_url: 视频URL
            interval_sec: 抽帧时间间隔(秒),默认1秒
        Returns:
            frames: base64编码的图片列表
        """
        cap = cv2.VideoCapture(video_url)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_sec)
        frames = []
        frame_count = 0

        prev_frame = None
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 按时间间隔抽帧
            if frame_count % frame_interval == 0:
                # 检测场景变化
                if prev_frame is not None:
                    diff = cv2.absdiff(frame, prev_frame)
                    change = np.mean(diff)
                    # 如果场景变化明显,保存该帧
                    if change > 30:  # 可调整阈值
                        _, buffer = cv2.imencode('.jpg', frame)
                        base64_frame = base64.b64encode(buffer).decode('utf-8')
                        frames.append(f"data:image/jpeg;base64,{base64_frame}")
                else:
                    # 保存第一帧
                    _, buffer = cv2.imencode('.jpg', frame)
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    frames.append(f"data:image/jpeg;base64,{base64_frame}")

                prev_frame = frame.copy()

            frame_count += 1

        cap.release()
        return frames
