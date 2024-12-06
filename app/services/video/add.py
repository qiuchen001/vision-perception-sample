from app.dao.video_dao import VideoDAO
from app.services.video.mining import MiningVideoService
from app.services.video.summary import SummaryVideoService
from app.utils.embedding import *


class AddVideoService:
    def __init__(self):
        self.video_dao = VideoDAO()

    @staticmethod
    def parse_mining_result(mining_results):
        tags = []
        for item in mining_results:
            tag = item["behaviour"]["behaviourName"]
            tags.append(tag)
        return tags


    @staticmethod
    def parse_summary_result(summary_result):
        return summary_result['summary']


    def add(self, video_url, action_type):
        video_info = self.video_dao.get_by_path(video_url)
        print(f"video_info: {video_info}")
        if len(video_info) == 0:
            raise ValueError("未找到视频信息")

        video = video_info[0]

        if action_type == 1: # 1. 挖掘 2. 提取摘要 3. 挖掘及提取摘要
            mining_service = MiningVideoService()
            mining_result = mining_service.mining(video_url)
            tags = self.parse_mining_result(mining_result)
            video['tags'] = tags
        elif action_type == 2:
            summary_service = SummaryVideoService()
            summary_result = summary_service.summary(video_url)
            summary_txt = self.parse_summary_result(summary_result)
            video['summary_txt'] = summary_txt
            video['embedding'] = embed_fn(summary_txt)
        elif action_type == 3:
            mining_service = MiningVideoService()
            mining_result = mining_service.mining(video_url)
            tags = self.parse_mining_result(mining_result)
            video['tags'] = tags

            summary_service = SummaryVideoService()
            summary_result = summary_service.summary(video_url)
            summary_txt = self.parse_summary_result(summary_result)
            video['summary_txt'] = summary_txt
            video['embedding'] = embed_fn(summary_txt)
        else:
            raise ValueError("无效的操作类型")

        self.video_dao.upsert_video(video)

        return video['m_id']





