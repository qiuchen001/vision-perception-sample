from typing import List, Tuple, Union
from PIL import Image
import os

from app.utils.clip_embeding import clip_embedding
from app.utils.milvus_operator import video_frame_operator


def _process_search_results(results) -> Tuple[List[str], List[int]]:
    """
    处理搜索结果。

    Args:
        results: Milvus 搜索返回的结果

    Returns:
        Tuple[List[str], List[int]]: 视频路径和时间戳列表
    """
    video_paths = []
    at_seconds = []
    for result in results:
        video_id = result.get('video_id')
        timestamp = result.get('at_seconds')
        if video_id is not None and timestamp is not None:
            video_paths.append(video_id)
            at_seconds.append(timestamp)
    return video_paths, at_seconds


def video_search(query: Union[str, Image.Image, str]) -> Tuple[List[str], List[int]]:
    """
    通过文本或图片搜索视频。

    Args:
        query: 可以是文本字符串、PIL.Image 对象或图片路径

    Returns:
        Tuple[List[str], List[int]]: 返回视频路径列表和对应的时间戳列表
    """
    if query is None:
        print("没有任何输入！")
        return [], []

    try:
        # 根据输入类型生成向量
        if isinstance(query, str):
            if os.path.isfile(query):  # 如果是图片路径
                try:
                    image = Image.open(query).convert('RGB')
                    input_embedding = clip_embedding.embedding_image(image)
                except Exception as e:
                    print(f"读取图片失败: {str(e)}")
                    return [], []
            else:  # 文本查询
                input_embedding = clip_embedding.embedding_text(query)
        elif isinstance(query, Image.Image):
            input_embedding = clip_embedding.embedding_image(query)
        else:
            print(f"不支持的查询类型: {type(query)}")
            return [], []

        if input_embedding is None or len(input_embedding) == 0:
            print("无法生成查询向量")
            return [], []

        # 转换向量格式
        input_embedding = input_embedding[0].detach().cpu().numpy()
        input_embedding = input_embedding.astype('float32')

        print("input_embedding shape:", input_embedding.shape)

        # 执行搜索
        results = video_frame_operator.search_data(
            embedding=input_embedding,
            output_fields=['video_id', 'at_seconds']
        )

        print("找到结果数量:", len(results))

        return _process_search_results(results)

    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return [], []


def image_to_video(image_path: str) -> Tuple[List[str], List[int]]:
    """
    通过图片搜索视频（便捷方法）。

    Args:
        image_path: 图片文件路径

    Returns:
        Tuple[List[str], List[int]]: 返回视频路径列表和对应的时间戳列表
    """
    return video_search(image_path)


def text_to_video(text: str) -> Tuple[List[str], List[int]]:
    """
    通过文本搜索视频（便捷方法）。

    Args:
        text: 搜索文本

    Returns:
        Tuple[List[str], List[int]]: 返回视频路径列表和对应的时间戳列表
    """
    return video_search(text)


if __name__ == "__main__":
    # 文本搜索示例
    print("\n=== 文本搜索测试 ===")
    video_paths, at_seconds = text_to_video("高速路")
    print("文本搜索结果:")
    print("视频路径:", video_paths)
    print("时间戳:", at_seconds)

    # 图片搜索示例
    print("\n=== 图片搜索测试 ===")
    image_path = r"E:\workspace\ai-ground\dataset\traffic\CAM_BACK\1537295813887.jpg"  # 替换为实际的测试图片路径
    if os.path.exists(image_path):
        video_paths, at_seconds = image_to_video(image_path)
        print("图片搜索结果:")
        print("视频路径:", video_paths)
        print("时间戳:", at_seconds)