import os
from typing import Optional
import torch
# import cn_clip.clip as clip
import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models
from PIL import Image
from config import Config


# # 从视频中提取帧，并跳过指定数量的帧。
# def extract_frames(video_path, N):
#     video_frames = []
#     capture = cv2.VideoCapture(video_path)
#     fps = capture.get(cv2.CAP_PROP_FPS)
#     current_frame = 0
#
#     while capture.isOpened():
#         ret, frame = capture.read()
#         if ret:
#             video_frames.append(Image.fromarray(frame[:, :, ::-1]))
#         else:
#             break
#         current_frame += N
#         capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
#
#     capture.release()
#     return video_frames, fps
#
# def embedding_video(video_path, N):
#     print(f"Processing video: {video_path}")
#
#     idxs, embeddings, paths, at_seconds = [], [], [], []
#
#     total_count = 0
#
#     try:
#         video_frames, fps = extract_frames(video_path, N)
#         for frame_idx, frame in enumerate(video_frames):
#             frame_embedding = clip_embeding.embeding_image(frame)
#
#             idxs.append(total_count)
#             embeddings.append(frame_embedding[0].detach().cpu().numpy().tolist())
#             paths.append(video_path)
#             # Calculate the timestamp in seconds for each frame
#             timestamp = int((frame_idx * N) / fps)
#             at_seconds.append(np.int32(timestamp))
#             total_count += 1
#
#             if total_count % 50 == 0:
#                 data = [idxs, embeddings, paths, at_seconds]
#                 print(f'Successfully inserted {operator.coll_name} items: {len(idxs)}')
#                 idxs, embeddings, paths, at_seconds = [], [], [], []
#
#     except Exception as e:
#         print(f"Error processing video {video_path}: {e}")


class ClipEmbeding:
    device = "cuda" if torch.cuda.is_available() else "cpu"

    def __init__(self):
        self.model, self.processor = load_from_name(
            name=Config.CN_CLIP_MODEL_PATH,
            device=self.device,
            vision_model_name="ViT-L-14-336",
            text_model_name="RoBERTa-wwm-ext-base-chinese",
            input_resolution=336)
        self.model.eval()
        self.tokenizer = clip.tokenize

    def probs(self, image: Image):
        process_image = self.processor(image).unsqueeze(0).to(self.device)
        text = self.tokenizer(["a diagram", "a dog", "a cat"]).to(self.device)

        with torch.no_grad():
            logits_per_image, logits_per_text = self.model(process_image, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()

        print("Label probs:", probs)

    def match(self, image: Image, desc: str):
        process_image = self.processor(image).unsqueeze(0).to(self.device)
        text = self.tokenizer([desc]).to(self.device)

        with torch.no_grad():
            logits_per_image, logits_per_text = self.model(process_image, text)
            similarity = str(logits_per_image)[9:13]
            res = float(similarity)
            return res

    def embedding_image(self, image: Image):
        process_image = self.processor(image).unsqueeze(0).to(self.device)
        image_features = self.model.encode_image(process_image)
        return image_features

    def embedding_text(self, text: str):
        text = self.tokenizer([text]).to(self.device)
        text_features = self.model.encode_text(text)
        return text_features

    def embedding(self, image: Image, text: str):
        process_image = self.processor(image).unsqueeze(0).to(self.device)
        text = self.tokenizer([text]).to(self.device)

        image_features = self.model.encode_image(process_image)
        text_features = self.model.encode_text(text)
        return image_features, text_features


clip_embedding = ClipEmbeding()

if __name__ == "__main__":
    image_path = r"E:\playground\ai\datasets\bdd100k\bdd100k\images\10k\train\00a7ef03-00000000.jpg"

    pil_image = Image.open(image_path)
    # clip_embedding.probs(pil_image)

    # match = clip_embedding.match(pil_image, "a cat")
    # print(match)

    image_embeddings = clip_embedding.embedding_image(pil_image)
    print(len(image_embeddings[0]))

    # res = image_embeddings[0].detach().numpy().tolist()
    #
    # print(type(res))
    #
    # print(res)

    # embedding = clip_embedding.embedding_text("a cat")
    # print(len(embedding[0]))
