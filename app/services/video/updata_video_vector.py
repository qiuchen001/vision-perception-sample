import math
import cv2
import torch
import numpy as np
from PIL import Image
import os
import uuid

from app.utils.clip_embeding import clip_embedding
from app.utils.milvus_operator import video_frame_operator, MilvusOperator
from config import Config

N = Config.VIDEO_FRAME_INTERVAL


# 从视频中提取帧，并跳过指定数量的帧。
def extract_frames(video_path, N):
    video_frames = []
    capture = cv2.VideoCapture(video_path)
    fps = capture.get(cv2.CAP_PROP_FPS)
    current_frame = 0

    while capture.isOpened():
        ret, frame = capture.read()
        if ret:
            video_frames.append(Image.fromarray(frame[:, :, ::-1]))
        else:
            break
        current_frame += N
        capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    capture.release()
    return video_frames, fps


# 使用CLIP模型对帧进行编码。
def encode_frames(video_frames, model, preprocess, device, batch_size=256):
    batches = math.ceil(len(video_frames) / batch_size)
    video_features = torch.empty([0, 512], dtype=torch.float16).to(device)

    for i in range(batches):
        batch_frames = video_frames[i * batch_size: (i + 1) * batch_size]
        batch_preprocessed = torch.stack([preprocess(frame) for frame in batch_frames]).to(device)
        with torch.no_grad():
            batch_features = model.encode_image(batch_preprocessed)
            batch_features /= batch_features.norm(dim=-1, keepdim=True)
        video_features = torch.cat((video_features, batch_features))

    return video_features


def process_single_image(image_path: str, operator: MilvusOperator, id_start: int = 0) -> None:
    """处理单张图片并插入向量数据库
    
    Args:
        image_path: 图片文件路径
        operator: Milvus操作器实例
        id_start: 起始ID号(已废弃，保留参数仅用于兼容)
    """
    try:
        image = Image.open(image_path).convert('RGB')
        embedding = clip_embedding.embedding_image(image)
        
        data = [[str(uuid.uuid4())],  # 使用 UUID 替代递增 ID
                [embedding[0].detach().cpu().numpy().tolist()],
                [image_path]]
        
        operator.insert_data(data)
        print(f'成功插入图片向量: {image_path}')
    except Exception as e:
        print(f'处理图片失败 {image_path}: {e}')


def update_image_vector(data_path: str, operator: MilvusOperator) -> None:
    """处理文件夹中的所有图片"""
    m_ids, embeddings, paths = [], [], []
    
    # 检查是否为单个文件
    if os.path.isfile(data_path):
        process_single_image(data_path, operator)
        return
        
    # 处理文件夹
    for dir_name in os.listdir(data_path):
        sub_dir = os.path.join(data_path, dir_name)
        if not os.path.isdir(sub_dir):
            continue
            
        for file in os.listdir(sub_dir):
            try:
                image_path = os.path.join(sub_dir, file)
                image = Image.open(image_path).convert('RGB')
                embedding = clip_embedding.embedding_image(image)

                m_ids.append(str(uuid.uuid4()))  # 使用 UUID
                embeddings.append(embedding[0].detach().cpu().numpy().tolist())
                paths.append(image_path)

                # 每50个批量插入一次
                if len(m_ids) >= 50:
                    operator.insert_data([m_ids, embeddings, paths])
                    print(f'成功批量插入 {operator.coll_name} 条目数: {len(m_ids)}')
                    m_ids, embeddings, paths = [], [], []

            except Exception as e:
                print(f'处理图片失败 {image_path}: {e}')
                continue

    # 处理剩余数据
    if m_ids:
        operator.insert_data([m_ids, embeddings, paths])
        print(f'成功批量插入最后的 {operator.coll_name} 条目数: {len(m_ids)}')


def process_single_video(video_path: str, operator: MilvusOperator, N: int, id_start: int = 0) -> None:
    """处理单个视频文件并插入向量数据库
    
    Args:
        video_path: 视频文件路径或URL
        operator: Milvus操作器实例
        N: 帧间隔
        id_start: 起始ID号(已废弃，保留参数仅用于兼容)
    """
    m_ids, embeddings, paths, at_seconds = [], [], [], []
    
    try:
        # 判断是否为URL
        if video_path.startswith(('http://', 'https://')):
            capture = cv2.VideoCapture(video_path)
            if not capture.isOpened():
                raise Exception("无法打开在线视频流")
        else:
            if not os.path.exists(video_path):
                raise Exception("本地视频文件不存在")
            capture = cv2.VideoCapture(video_path)
            
        fps = capture.get(cv2.CAP_PROP_FPS)
        current_frame = 0
        video_frames = []
        
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            video_frames.append(Image.fromarray(frame[:, :, ::-1]))
            current_frame += N
            capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            
        capture.release()
        
        # 处理每一帧
        for frame_idx, frame in enumerate(video_frames):
            frame_embedding = clip_embedding.embedding_image(frame)
            
            m_ids.append(str(uuid.uuid4()))  # 使用 UUID
            embeddings.append(frame_embedding[0].detach().cpu().numpy().tolist())
            paths.append(video_path)
            timestamp = int((frame_idx * N) / fps)
            at_seconds.append(np.int32(timestamp))
            
            # 每50帧批量插入一次
            if len(m_ids) >= 50:
                data = [m_ids, embeddings, paths, at_seconds]
                operator.insert_data(data)
                print(f'成功插入 {operator.coll_name} 条目数: {len(m_ids)}')
                m_ids, embeddings, paths, at_seconds = [], [], [], []
                
        # 处理剩余数据
        if m_ids:
            data = [m_ids, embeddings, paths, at_seconds]
            operator.insert_data(data)
            print(f'成功插入 {operator.coll_name} 条目数: {len(m_ids)}')
            
    except Exception as e:
        print(f'处理视频失败 {video_path}: {e}')


def update_video_vector(data_path: str, operator: MilvusOperator, N: int) -> None:
    """处理文件夹中的所有视频
    
    Args:
        data_path: 视频文件夹路径
        operator: Milvus操作器实例
        N: 帧间隔
    """
    # 检查是否为单个文件
    if os.path.isfile(data_path):
        process_single_video(data_path, operator, N)
        return
        
    for file in os.listdir(data_path):
        video_path = os.path.join(data_path, file)
        if not os.path.isfile(video_path):
            continue
            
        print(f"处理视频: {video_path}")
        process_single_video(video_path, operator, N)

    print(f'完成更新 {operator.coll_name}')


if __name__ == '__main__':
    data_dir = r'E:\workspace\ai-ground\dataset\videos'
    # data_dir = r'E:\workspace\work_data\videos'
    # data_dir = r'E:\workspace\ai-ground\dataset\traffic'
    # update_image_vector(data_dir, video_frame_operator)
    # update_video_vector(data_dir, video_frame_operator, N=120)

    # process_single_image("path/to/image.jpg", video_frame_operator)

    # 处理整个文件夹
    # update_image_vector(r"E:\workspace\ai-ground\dataset\traffic", video_frame_operator)


    # 处理单个视频
    # process_single_video(r"E:\workspace\work_data\videos\120266-720504932_small.mp4", video_frame_operator, N=120)
    process_single_video("http://10.66.12.37:30946/perception-mining/b7ec1001240181ceb5ec3e448c7f9b78.mp4", video_frame_operator, N=120)

    # 处理整个文件夹
    # update_video_vector(r"E:\workspace\work_data\videos", video_frame_operator, N=120)

