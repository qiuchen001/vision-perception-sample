import math
import cv2
import torch
import numpy as np
from PIL import Image
import os

from app.utils.clip_embeding import clip_embedding
from app.utils.milvus_operator import text_video_vector, MilvusOperator

N = 30


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


def update_video_vector(data_path, operator: MilvusOperator, N):
    m_ids, embeddings, paths, at_seconds = [], [], [], []

    total_count = 0
    for file in os.listdir(data_path):
        video_path = os.path.join(data_path, file)
        print(f"Processing video: {video_path}")

        try:
            video_frames, fps = extract_frames(video_path, N)
            for frame_idx, frame in enumerate(video_frames):
                frame_embedding = clip_embedding.embedding_image(frame)

                m_ids.append(total_count)
                embeddings.append(frame_embedding[0].detach().cpu().numpy().tolist())
                paths.append(video_path)
                # Calculate the timestamp in seconds for each frame
                timestamp = int((frame_idx * N) / fps)
                at_seconds.append(np.int32(timestamp))
                total_count += 1

                if total_count % 50 == 0:
                    data = [m_ids, embeddings, paths, at_seconds]
                    operator.insert_data(data)
                    print(f'Successfully inserted {operator.coll_name} items: {len(m_ids)}')
                    m_ids, embeddings, paths, at_seconds = [], [], [], []

        except Exception as e:
            print(f"Error processing video {video_path}: {e}")

    if len(m_ids):
        data = [m_ids, embeddings, paths, at_seconds]
        operator.insert_data(data)
        print(f'Successfully inserted {operator.coll_name} items: {len(m_ids)}')

    print(f'Finished updating {operator.coll_name} items: {total_count}')


def update_image_vector(data_path, operator: MilvusOperator):
    m_ids, embeddings, paths = [], [], []

    total_count = 0
    for dir_name in os.listdir(data_path):
        sub_dir = os.path.join(data_path, dir_name)
        for file in os.listdir(sub_dir):

            image = Image.open(os.path.join(sub_dir, file)).convert('RGB')
            embedding = clip_embedding.embedding_image(image)

            m_ids.append(total_count)
            embeddings.append(embedding[0].detach().cpu().numpy().tolist())

            paths.append(os.path.join(sub_dir, file))
            total_count += 1

            if total_count % 50 == 0:
                data = [m_ids, embeddings, paths]
                operator.insert_data(data)

                print(f'success insert {operator.coll_name} items:{len(m_ids)}')
                m_ids, embeddings, paths = [], [], []

        if len(m_ids):
            data = [m_ids, embeddings, paths]
            operator.insert_data(data)
            print(f'success insert {operator.coll_name} items:{len(m_ids)}')

    print(f'finish update {operator.coll_name} items: {total_count}')


if __name__ == '__main__':
    data_dir = r'E:\workspace\ai-ground\dataset\videos'
    # data_dir = r'E:\workspace\work_data\videos'
    # data_dir = r'E:\workspace\ai-ground\dataset\traffic'
    # update_image_vector(data_dir, text_video_vector)
    update_video_vector(data_dir, text_video_vector, N=120)

