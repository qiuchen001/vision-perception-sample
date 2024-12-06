from pymilvus import MilvusClient
from ..models.video import Video
from ..utils.logger import logger
import uuid
from flask import current_app

class VideoDAO:
    def __init__(self):
        self.milvus_client = MilvusClient(uri="http://10.66.12.37:19530", db_name="summary_video_db")
        # self.milvus_client = current_app.config['MILVUS_CLIENT']
        self.collection_name = "video_collection"
        self.schema = Video.create_schema()
        Video.create_collection(self.collection_name, self.schema)
        Video.create_index(self.collection_name)

    def get_all_videos(self):
        logger.info(f"Querying all users from collection: {self.collection_name}")
        return self.milvus_client.query(self.collection_name, filter="", limit = 6)

    def insert_video(self, user):
        user_data = {
            "m_id": user.m_id,
            "embedding": user.embedding,
            "path": user.path,
            "thumbnail_path": user.thumbnail_path,
            "summary_txt": user.summary_txt,
            "tags": str(user.tags)  # 将数组转换为字符串
        }
        self.milvus_client.insert(self.collection_name, [user_data])

    def check_url_exists(self, url):
        # 检查URL是否存在
        # 返回True或False
        query_result = self.milvus_client.query(self.collection_name, filter=f"path == '{url}'", limit=1)
        return len(query_result) > 0


    def get_by_path(self, url):
        query_result = self.milvus_client.query(self.collection_name, filter=f"path == '{url}'", limit=1)
        return query_result


    def insert_url(self, url, embedding):
        # 插入URL到数据库
        video_data = {
            "m_id": str(uuid.uuid4()),
            "embedding": embedding,
            "path": url,
            "thumbnail_path": None,
            "summary_txt": None,
            "tags": None
        }
        self.milvus_client.insert(self.collection_name, [video_data])

    def upsert_video(self, video):
        user_data = {
            "m_id": video['m_id'],
            "embedding": video['embedding'],
            "path": video['path'],
            "thumbnail_path": video['thumbnail_path'],
            "summary_txt": video['summary_txt'],
            "tags": video['tags']
        }
        self.milvus_client.upsert(self.collection_name, [user_data])

    def search_video(self, embedding):
        search_params = {
            "metric_type": "IP",  # 指定相似度度量类型，IP表示内积（Inner Product）
            "offset": 0,  # 搜索结果的偏移量，从第0个结果开始
            "ignore_growing": False,  # 是否忽略正在增长的索引，False表示不忽略
            "params": {"nprobe": 16}  # 搜索参数，nprobe表示要探测的聚类数
        }

        result = self.milvus_client.search(
            collection_name=self.collection_name,  # 指定搜索的集合名称
            anns_field="embedding",  # 指定用于搜索的字段，这里是embedding字段
            data=[embedding],  # 要搜索的向量数据
            limit=6,  # 返回的最大结果数
            search_params=search_params,  # 搜索参数
            output_fields=['m_id', 'path', 'summary_txt', 'tags'],  # 指定返回的字段
            consistency_level="Strong"  # 一致性级别，Strong表示强一致性
        )
        return result

