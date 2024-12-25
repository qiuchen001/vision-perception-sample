"""
Milvus 数据库操作工具类。
提供与 Milvus 数据库交互的基础操作，支持多集合和多数据库配置。
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pymilvus import connections, db, Collection, utility

# 加载环境变量
load_dotenv()


class MilvusOperator:
    _instances: Dict[str, 'MilvusOperator'] = {}
    _VALID_METRIC_TYPES = {'L2', 'IP'}  # 有效的度量类型集合

    def __init__(
            self,
            database: str,
            collection: str,
            metric_type: str = 'IP',  # 默认使用 IP
            host: Optional[str] = None,
            port: Optional[str] = None
    ):
        """
        初始化 Milvus 操作器。

        Args:
            database: 数据库名称
            collection: 集合名称
            metric_type: 度量类型 ('L2'|'IP')，默认为'IP'
            host: Milvus 服务器地址，默认从环境变量获取
            port: Milvus 服务器端口，默认从环境变量获取

        Raises:
            ValueError: 当 metric_type 不是有效值时抛出
        """
        if metric_type not in self._VALID_METRIC_TYPES:
            raise ValueError(f"无效的度量类型: {metric_type}。必须是 {self._VALID_METRIC_TYPES} 之一")

        self.database = database
        self.coll_name = collection
        self.metric_type = metric_type

        # 使用环境变量或传入参数配置连接信息
        self.host = host or os.getenv('MILVUS_HOST', '127.0.0.1')
        self.port = port or os.getenv('MILVUS_PORT', '19530')

        self._connect()

    def _connect(self) -> None:
        """建立与 Milvus 的连接"""
        try:
            connections.connect(
                # alias=f"{self.database}_{self.coll_name}",
                alias="default",
                host=self.host,
                port=self.port
            )
            db.using_database(self.database)
        except Exception as e:
            raise ConnectionError(f"连接 Milvus 失败: {str(e)}")

    @classmethod
    def get_instance(
            cls,
            database: str,
            collection: str,
            metric_type: str = 'IP',  # 这里也添加默认值
            **kwargs
    ) -> 'MilvusOperator':
        """
        获取 MilvusOperator 实例（单例模式）。

        Args:
            database: 数据库名称
            collection: 集合名称
            metric_type: 度量类型，默认为'IP'
            **kwargs: 其他配置参数

        Returns:
            MilvusOperator 实例
        """
        instance_key = f"{database}_{collection}"
        if instance_key not in cls._instances:
            cls._instances[instance_key] = cls(database, collection, metric_type, **kwargs)
        return cls._instances[instance_key]

    def insert_data(self, data: List[Dict[str, Any]]) -> None:
        """
        插入数据到集合。

        Args:
            data: 要插入的数据列表
        """
        try:
            collection = Collection(self.coll_name)
            collection.insert(data)
        except Exception as e:
            raise Exception(f"插入数据失败: {str(e)}")

    def search_data(
            self,
            embedding: List[float],
            limit: int = 5,
            output_fields: Optional[List[str]] = None,
            expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量。

        Args:
            embedding: 查询向量
            limit: 返回结果数量
            output_fields: 返回字段列表
            expr: 过滤表达式

        Returns:
            搜索结果列表
        """
        try:
            collection = Collection(self.coll_name)
            collection.load()

            search_params = {
                "metric_type": self.metric_type,
                "offset": 0,
                "ignore_growing": False,
                "params": {"nprobe": 5}
            }

            results = collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=output_fields or ['m_id', 'video_id', 'at_seconds'],
                consistency_level="Strong"
            )

            return self._format_search_results(results)
        except Exception as e:
            print(f"搜索数据失败: {str(e)}")  # 添加错误日志
            return []  # 发生错误时返回空列表
        finally:
            try:
                collection.release()
            except Exception:
                pass  # 忽略释放时的错误

    def _format_search_results(self, results) -> List[Dict[str, Any]]:
        """
        格式化搜索结果。
        
        Args:
            results: Milvus 搜索返回的结果对象
            
        Returns:
            List[Dict[str, Any]]: 格式化后的结果列表
        """
        entity_list = []
        if results and results[0]:
            for hits in results:  # 遍历每个查询的结果
                for hit in hits:  # 遍历每个匹配项
                    entity = {
                        'm_id': hit.id,  # 使用 hit.id 替代 ids[idx]
                        'distance': hit.distance,  # 使用 hit.distance 替代 distances[idx]
                    }
                    
                    # 添加实体的其他字段
                    if hasattr(hit, 'entity'):
                        entity['video_id'] = hit.entity.get('video_id')
                        entity['at_seconds'] = hit.entity.get('at_seconds')
                    
                    entity_list.append(entity)

            # 按距离升序排序
            entity_list.sort(key=lambda x: x['distance'])
        
        return entity_list

    def query_by_ids(self, ids: List[str], output_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        通过ID查询数据。

        Args:
            ids: ID列表
            output_fields: 返回字段列表

        Returns:
            查询结果列表
        """
        try:
            collection = Collection(self.coll_name)
            collection.load()

            ids_str = ', '.join(str(id) for id in ids)
            expr = f'm_id in [{ids_str}]'

            return collection.query(
                expr=expr,
                output_fields=output_fields or ["m_id", "embedding", "video_id"],
                limit=len(ids)
            )
        except Exception as e:
            raise Exception(f"查询数据失败: {str(e)}")
        finally:
            collection.release()

    def delete_by_ids(self, ids: List[str]) -> None:
        """
        通过ID删除数据。

        Args:
            ids: 要删除的ID列表
        """
        try:
            collection = Collection(self.coll_name)
            collection.load()

            ids_str = ', '.join(str(id) for id in ids)
            expr = f'm_id in [{ids_str}]'
            collection.delete(expr)
        except Exception as e:
            raise Exception(f"删除数据失败: {str(e)}")
        finally:
            collection.release()


# 示例使用方式
# text_video_vector = MilvusOperator.get_instance(
#     database='text_video_db',
#     collection='text_video_vector',
#     metric_type='IP'
# )

# 使用默认的 IP 度量类型
video_frame_operator = MilvusOperator.get_instance(
    database='video_db',
    collection='video_frame_vector_v2'
)
