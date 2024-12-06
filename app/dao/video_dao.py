from pymilvus import MilvusClient
from ..models.video import Video
from ..utils.logger import logger

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