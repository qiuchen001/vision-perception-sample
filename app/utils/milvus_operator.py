from pymilvus import connections, db, Collection


class MilvusOperator:
    def __init__(self, database, collection, metric_type):
        self.database = database
        self.coll_name = collection
        self.metric_type = metric_type
        self.connect = connections.connect(alias="default", host='10.66.12.37', port='19530')
        db.using_database(database)

    def insert_data(self, data):
        collection = Collection(self.coll_name)
        mr = collection.insert(data)

    def search_data(self, embeding):
        collection = Collection(self.coll_name)
        collection.load()

        search_params = {
            "metric_type": self.metric_type,
            "offset": 0,
            "ignore_growing": False,
            "params": {"nprobe": 5}
        }

        results = collection.search(
            data=[embeding],
            anns_field="embeding",
            param=search_params,
            limit=5,
            expr=None,
            output_fields=['m_id', 'video_id', 'at_seconds'],
            consistency_level="Strong"
        )
        entity_list = []
        if results[0] is not None:
            for idx in range(len(results[0])):
                hit = results[0][idx]

                entity_list.append({'m_id': results[0].ids[idx],
                                    'distance': results[0].distances[idx],
                                    'video_id': hit.entity.get('video_id'),
                                    'at_seconds': hit.entity.get('at_seconds'),
                                    })
            # Sort the entity_list by distance in ascending order
            entity_list.sort(key=lambda x: x['distance'], reverse=False)

        return entity_list

    def query_by_ids(self, ids: list):
        collection = Collection(self.coll_name)
        collection.load()

        str_list = [str(id) for id in ids]
        temp_str = ', '.join(str_list)
        query_expr = f'M_id in [{temp_str}]'

        res = collection.query(
            expr=query_expr,
            offset=0,
            limit=16384,
            output_fields=["m_id", "embeding", "video_id"],
        )

        return res

    def delete_by_ids(self, ids: list):
        collection = Collection(self.coll_name)
        collection.load()

        str_list = [str(id) for id in ids]
        temp_str = ', '.join(str_list)
        query_expr = f'm_id in [{temp_str}]'
        collection.delete(query_expr)
        return


text_video_vector = MilvusOperator('text_video_db', 'text_video_vector', 'IP')