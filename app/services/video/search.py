from app.dao.video_dao import VideoDAO
from app.utils.embedding import *


class SearchVideoService:
    def __init__(self):
        self.video_dao = VideoDAO()

    def parse_search_result(self, search_result):
        video_list = []
        if search_result[0] is not None:
            for idx in range(len(search_result[0])):
                hit = search_result[0][idx]
                entity = hit.get('entity')

                video_info = {
                    'm_id': hit['id'],
                    'distance': hit['distance'],
                    'path': entity.get('path'),
                    'summary_txt': entity.get('summary_txt'),
                    'tags': list(entity.get("tags", [])),  # 将 RepeatedScalarContainer 转换为列表

                }
                video_list.append(video_info)
        return video_list


    def search(self, txt):
        embedding = embed_fn(txt)

        search_result =  self.video_dao.search_video(embedding)

        return self.parse_search_result(search_result)

