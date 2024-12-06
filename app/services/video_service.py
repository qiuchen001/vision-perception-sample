from ..dao.video_dao import VideoDAO
from ..utils.logger import logger
from werkzeug.utils import secure_filename
import os
from ..utils.common import *
import json
from ..prompt import mining
from openai import OpenAI

class VideoService:
    def __init__(self):
        self.video_dao = VideoDAO()

    def get_all_videos(self):
        logger.info("Fetching all users")
        return self.video_dao.get_all_videos()

    def upload(self, video_file):
        filename = secure_filename(video_file.filename)
        video_file_path = os.path.join('/tmp', filename)
        video_file.save(video_file_path)

        try:
            return upload_thumbnail_to_oss(filename, video_file_path)
        finally:
            os.remove(video_file_path)
            logger.debug(f"Deleted temporary file: {video_file_path}")


    def mining(self, video_url):
        mining_result = self.mining_video_handler(video_url)
        js = json.loads(mining_result)
        content = js['choices'][0]['message']['content']
        mining_json = self.parse_json_string(content)
        return self.format_mining_result(mining_json, video_url)

    def seconds_to_time_format(self, total_seconds):
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02}:{seconds:02}"


    def time_to_standard_format(self, time_range_str):
        start_time_str, end_time_str = time_range_str.split('-')
        start_seconds = self.time_to_seconds(start_time_str)
        end_seconds = self.time_to_seconds(end_time_str)
        start_time_formatted = self.seconds_to_time_format(start_seconds)
        end_time_formatted = self.seconds_to_time_format(end_seconds)
        return start_time_formatted, end_time_formatted


    def time_to_seconds(self, time_str):
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError("时间格式不正确，应为 '0:13' 或 '1:23:45'")


    def format_mining_result(self, mining_result, video_url):
        mining_result_new = []
        for item in mining_result:
            if item['behaviour']['behaviourId'] is None or item['behaviour']['behaviourName'] is None or \
                    item['behaviour']['timeRange'] is None:
                continue

            if len(item['behaviour']['timeRange'].split('-')) < 2:
                continue

            start_time_formatted, end_time_formatted = self.time_to_standard_format(item['behaviour']['timeRange'])
            time_range_str = f"{start_time_formatted}-{end_time_formatted}"
            item['behaviour']['timeRange'] = time_range_str
            start_time = self.time_to_seconds(start_time_formatted)
            thumbnail_file_name = os.path.basename(video_url) + "_t_" + str(start_time) + ".jpg"
            thumbnail_local_path = os.path.join('/tmp', thumbnail_file_name)
            generate_thumbnail_from_video(video_url, thumbnail_local_path, start_time)
            item['thumbnail_url'] = upload_thumbnail_to_oss(thumbnail_file_name, thumbnail_local_path)
            mining_result_new.append(item)
            os.remove(thumbnail_local_path)
        return mining_result_new


    def parse_json_string(self, json_str):
        cleaned_str = json_str.replace('\\n', '').replace('\\"', '"')
        cleaned_str = cleaned_str.strip('```json')
        parsed_data = json.loads(cleaned_str)
        return parsed_data


    def mining_video_handler(self, video_url):
        model_name = "qwen-vl-max-latest"

        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )


        base64_images = extract_frames_and_convert_to_base64(video_url)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video",
                        "video": base64_images
                    },
                    {
                        "type": "text",
                        "text": mining.system_instruction + "\n" + mining.prompt
                    }
                ]
            }
        ]
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )
        return response.model_dump_json()
