from app.utils.video_processor import VideoProcessor
from app.prompt.summary import system_instruction, prompt
import os
import json
from openai import OpenAI


def parse_json_string(json_str):
    cleaned_str = json_str.replace('\\n', '').replace('\\"', '"')
    cleaned_str = cleaned_str.strip('```json')
    parsed_data = json.loads(cleaned_str)
    return parsed_data


class SummaryVideoService:
    def __init__(self):
        self.video_processor = VideoProcessor()
        
    def summary(self, video_url):
        """生成视频摘要"""
        # 1. 提取关键帧
        frame_urls = self.video_processor.extract_key_frames(video_url)
        
        # 2. 调用通义千问VL模型
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        messages = [{
            "role": "system",
            "content": system_instruction
        }, {
            "role": "user",
            "content": [
                {
                    "type": "video",
                    "video": frame_urls
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]

        response = client.chat.completions.create(
            model=os.getenv("VISION_MODEL_NAME"),
            messages=messages,
            response_format={"type": "json_object"}
        )
        response_json = response.model_dump_json()
        js = json.loads(response_json)
        content = js['choices'][0]['message']['content']
        mining_content_json = parse_json_string(content)
        return mining_content_json
