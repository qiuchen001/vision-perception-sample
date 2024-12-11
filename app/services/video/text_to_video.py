from app.utils.clip_embeding import clip_embedding
from app.utils.milvus_operator import video_frame_operator


def video_search(text):
    if text is None:
        print("没有任何输入！")
        return None

    # clip编码
    input_embedding = clip_embedding.embedding_text(text)
    input_embedding = input_embedding[0].detach().cpu().numpy()
    # 确保向量类型为float32
    input_embedding = input_embedding.astype('float32')

    print("input_embedding:", input_embedding)

    results = video_frame_operator.search_data(input_embedding)

    print("results:", results)

    video_paths = [result['video_id'] for result in results]
    at_seconds = [result['at_seconds'] for result in results]
    return video_paths, at_seconds


if __name__ == "__main__":
    video_paths, at_seconds = video_search("高速路")
    print(video_paths)
    print(at_seconds)