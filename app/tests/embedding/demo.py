import dashscope
import json
from http import HTTPStatus
from dotenv import load_dotenv
load_dotenv()
import os

import dashscope
import base64
import json
from http import HTTPStatus
# 读取图片并转换为Base64,实际使用中请将xxx.png替换为您的图片文件名或路径
image_path = "256_1.png"
with open(image_path, "rb") as image_file:
    # 读取文件并转换为Base64
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
# 设置图像格式
image_format = "png"  # 根据实际情况修改，比如jpg、bmp 等
image_data = f"data:image/{image_format};base64,{base64_image}"
# 输入数据
text = "通用多模态表征模型示例"
inputs = [{'image': image_data + text}]

# 调用模型接口
resp = dashscope.MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=inputs,
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)
if resp.status_code == HTTPStatus.OK:
    print(json.dumps(resp.output, ensure_ascii=False, indent=4))