import os
from pymilvus import DataType, MilvusClient
from dotenv import load_dotenv
load_dotenv()


SERVER_HOST = os.getenv("SERVER_HOST")
uri=f"http://{SERVER_HOST}:19530"
milvus_client = MilvusClient(uri=uri, db_name=os.getenv("DB_NAME"))
collection_name = "video_collection"

def create_schema():
  schema = milvus_client.create_schema(
    auto_id=False,
    enable_dynamic_fields=True,
    description="text to video retrieval by tag or txt",
  )

  schema.add_field(field_name="m_id", datatype=DataType.VARCHAR, is_primary=True, max_length=256, description="唯一ID")
  schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=512, description="视频详情embedding")
  schema.add_field(field_name="path", datatype=DataType.VARCHAR, max_length=256, description="视频地址")
  schema.add_field(field_name="thumbnail_path", datatype=DataType.VARCHAR, max_length=256, description="视频缩略图地址",
                   nullable=True)
  schema.add_field(field_name="summary_txt", datatype=DataType.VARCHAR, max_length=3072, description="视频详情",
                   nullable=True)
  schema.add_field(field_name="tags", datatype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=10,
                   max_length=256, description="视频标签", nullable=True)

  return schema


def create_collection(schema):
  milvus_client.create_collection(
    collection_name=collection_name,
    schema=schema,
  )

if __name__ == "__main__":
  schema = create_schema()
  create_collection(schema)