from pymilvus import MilvusClient
from ..models.video import Video
from ..utils.logger import logger
import uuid

class VideoDAO:
    def __init__(self):
        self.milvus_client = MilvusClient(uri="http://10.66.12.37:19530", db_name="summary_video_db")
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
