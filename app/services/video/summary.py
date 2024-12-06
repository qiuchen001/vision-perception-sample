from app.dao.video_dao import VideoDAO
from app.utils.common import *
import os
import json
from openai import OpenAI
from app.prompt import summary


def parse_json_string(json_str):
    cleaned_str = json_str.replace('\\n', '').replace('\\"', '"')
    cleaned_str = cleaned_str.strip('```json')
    parsed_data = json.loads(cleaned_str)
    return parsed_data


class SummaryVideoService:

    def summary(self, video_url):
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
                        "text": summary.system_instruction + "\n" + summary.prompt
                    }
                ]
            }
        ]

        model_name = "qwen-vl-max-latest"

        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )
        response_json = response.model_dump_json()
        js = json.loads(response_json)
        content = js['choices'][0]['message']['content']
        mining_content_json = parse_json_string(content)
        return mining_content_json
