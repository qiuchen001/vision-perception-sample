from app.dao.video_dao import VideoDAO
from app.utils.embedding import *


class SearchVideoService:
    def __init__(self):
        self.video_dao = VideoDAO()

    # @staticmethod
    # def parse_search_result(search_result):
    #     video_list = []
    #     if search_result[0] is not None:
    #         for idx in range(len(search_result[0])):
    #             hit = search_result[0][idx]
    #             entity = hit.get('entity')
    #
    #             tags = entity.get("tags")
    #             if tags is None:
    #                 tags = []
    #
    #             video_info = {
    #                 'm_id': hit['id'],
    #                 'distance': hit['distance'],
    #                 'path': entity.get('path'),
    #                 'thumbnail_path': entity.get('thumbnail_path'),
    #                 'summary_txt': entity.get('summary_txt'),
    #                 'tags': list(tags),  # 将 RepeatedScalarContainer 转换为列表
    #
    #             }
    #             video_list.append(video_info)
    #     return video_list


    @staticmethod
    def parse_search_result(search_result):
        video_list = []
        for item in search_result:
        # entity = hit.get('entity')

            tags = item.get("tags")
            if tags is None:
                tags = []

            video_info = {
                'm_id':item.get('m_id'),
                # 'distance': item['distance'],
                'path': item.get('path'),
                'thumbnail_path': item.get('thumbnail_path'),
                'summary_txt': item.get('summary_txt'),
                'tags': list(tags),  # 将 RepeatedScalarContainer 转换为列表

            }
            video_list.append(video_info)

        return video_list


    def search(self, txt, page, page_size):
        embedding = None
        if txt:
            embedding = embed_fn(txt)

        search_result = self.video_dao.search_video(embedding, page, page_size)

        return self.parse_search_result(search_result)

