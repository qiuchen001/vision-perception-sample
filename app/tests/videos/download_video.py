import os
import requests
from urllib.parse import urlparse
from app.utils.logger import logger


def get_video_id(url):
    """从URL中提取视频ID"""
    path = urlparse(url).path
    filename = os.path.basename(path)
    # 如果文件名带扩展名,去掉扩展名
    video_id = os.path.splitext(filename)[0]
    return video_id


def download_video(url, save_dir):
    """下载单个视频"""
    try:
        # 获取视频ID作为文件名
        video_id = get_video_id(url)
        save_path = os.path.join(save_dir, f"{video_id}.mp4")

        # 如果文件已存在,跳过下载
        if os.path.exists(save_path):
            logger.info(f"视频 {video_id} 已存在,跳过下载")
            return True

        # 发起请求下载视频
        logger.info(f"开始下载视频 {video_id}")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # 分块写入文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"视频 {video_id} 下载完成")
        return True

    except Exception as e:
        logger.error(f"下载视频 {url} 失败: {str(e)}")
        return False


def main():
    # 创建保存目录
    save_dir = "videos"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 读取视频URL列表
    with open("app/tests/video_url.txt", "r") as f:
        urls = f.read().splitlines()

    # 去重
    urls = list(set(urls))

    # 过滤掉空行
    urls = [url for url in urls if url.strip()]

    logger.info(f"共有 {len(urls)} 个不重复视频需要下载")

    # 下载视频
    success = 0
    for i, url in enumerate(urls, 1):
        logger.info(f"正在处理第 {i}/{len(urls)} 个视频")
        if download_video(url, save_dir):
            success += 1

    logger.info(f"下载完成,成功 {success} 个,失败 {len(urls) - success} 个")


if __name__ == "__main__":
    main()
