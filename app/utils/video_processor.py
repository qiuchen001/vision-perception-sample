import cv2
import base64
import numpy as np
from typing import List


class VideoProcessor:
    def extract_key_frames(self, video_url: str, min_frames: int = 4, max_frames: int = 80) -> List[str]:
        """提取视频关键帧
        Args:
            video_url: 视频URL
            min_frames: 最少帧数(默认4)
            max_frames: 最多帧数(默认80)
        Returns:
            frames: base64编码的图片列表
        """
        cap = cv2.VideoCapture(video_url)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算采样间隔,确保提取的帧数在范围内
        target_frames = min(max(min_frames, total_frames // 30), max_frames)
        frame_interval = max(1, total_frames // target_frames)
        
        frames = []
        frame_count = 0
        prev_frame = None
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # 按间隔采样
            if frame_count % frame_interval == 0:
                # 检测场景变化
                if prev_frame is not None:
                    diff = cv2.absdiff(frame, prev_frame)
                    change = np.mean(diff)
                    # 如果场景变化明显且未超过最大帧数限制,保存该帧
                    if change > 30 and len(frames) < max_frames:
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
            
            # 如果已经达到最大帧数,停止提取
            if len(frames) >= max_frames:
                break
                
        cap.release()
        
        # 如果提取的帧数少于最小要求,调整采样间隔重新提取
        if len(frames) < min_frames:
            cap = cv2.VideoCapture(video_url)
            new_interval = total_frames // min_frames
            frames = []
            frame_count = 0
            
            while cap.isOpened() and len(frames) < min_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % new_interval == 0:
                    _, buffer = cv2.imencode('.jpg', frame)
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    frames.append(f"data:image/jpeg;base64,{base64_frame}")
                    
                frame_count += 1
                
            cap.release()
            
        return frames
