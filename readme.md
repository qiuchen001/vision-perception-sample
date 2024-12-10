# 项目文档

## 项目概述
本项目是一个基于 Flask 框架的 Web 应用程序，主要用于视频分析和处理。项目实现了视频上传、视频摘要生成、视频行为分析等功能，并将分析结果存储在 Milvus 数据库中，以便后续检索和查询。

## 功能模块

### 1. 视频上传与处理
- **视频上传**：用户可以通过 API 上传视频文件，并将其存储在 MinIO 对象存储中。
- **视频处理**：上传的视频文件会被提取帧并转换为 Base64 编码，用于后续的分析和摘要生成。

### 2. 视频摘要生成
- **摘要生成**：通过调用 OpenAI 的 API，对视频内容进行分析并生成摘要。生成的摘要信息包括视频中的关键行为和时间范围。

### 3. 视频行为分析
- **行为分析**：通过分析视频帧，识别视频中的常见驾驶行为和其他交通参与者的行为，并将分析结果以 JSON 格式输出。

### 4. 数据库管理
- **Milvus 数据库**：使用 Milvus 数据库存储视频的元数据和分析结果，支持通过标签或文本进行视频检索。

## 技术栈
- **Flask**：Web 框架用于构建 API 和处理请求。
- **MinIO**：对象存储服务，用于存储视频文件。
- **OpenAI**：用于视频内容分析和摘要生成。
- **Milvus**：向量数据库，用于存储和检索视频分析结果。

## 安装与运行

### 1. 环境准备
确保已安装以下依赖：
- Python 3.8+
- Flask
- MinIO
- OpenAI
- Milvus

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
在项目根目录下创建 `.env` 文件，并添加以下内容：
```
SERVER_HOST=localhost
DASHSCOPE_API_KEY=your_api_key
OSS_BUCKET_NAME=your_bucket_name
```

### 4. 启动应用
```bash
python run.py
```

## API 文档

### 1. 上传视频
- **URL**: `/vision-analyze/video/upload`
- **Method**: POST
- **描述**: 上传视频文件到系统，并将其存储在 MinIO 对象存储中
- **Form Data**:
  - `video`: 视频文件（必填，支持格式：mp4）
- **Response Success**:
  ```json
  {
    "msg": "success",
    "code": 0,
    "data": {
      "file_name": "video_oss_url",  // MinIO中的文件路径
      "video_url": "video_oss_url"   // 可访问的视频URL
    }
  }
  ```
- **Response Error**:
  ```json
  {
    "error": "No video file provided"
  }
  ```
- **错误码**:
  - `400`: 请求参数错误（如未提供视频文件）
  - `500`: 服务器内部错误（如上传失败）
- **注意事项**:
  - 请确保上传的是有效的视频文件
  - 文件大小限制取决于服务器配置
  - 上传成功后返回的 URL 将用于后续的视频添加操作
- **处理流程**:
  1. 检查请求中是否包含视频文件
  2. 生成唯一的文件名
  3. 将视频文件上传到 MinIO 存储
  4. 返回文件的访问 URL
- **示例**:
  ```python
  import requests
  
  url = "http://127.0.0.1:30501/vision-analyze/video/upload"
  video_path = "path/to/your/video.mp4"
  
  with open(video_path, 'rb') as video_file:
      files = {
          'video': ('video.mp4', video_file, 'video/mp4')
      }
      response = requests.post(url, files=files)
  
  print(response.json())
  ```
- **curl 示例**:
  ```bash
  curl -X POST \
    http://127.0.0.1:30501/vision-analyze/video/upload \
    -H 'Content-Type: multipart/form-data' \
    -F 'video=@/path/to/your/video.mp4'
  ```

### 2. 添加视频
- **URL**: `/vision-analyze/video/add`
- **Method**: POST
- **描述**: 将上传的视频添加到系统中，并根据指定的操作类型进行视频分析
- **Form Data**:
  - `video_url`: 视频的 OSS URL（从上传接口返回的 video_url）
  - `action_type`: 操作类型（必填，整数）
    - `1`: 仅进行视频行为挖掘
    - `2`: 仅生成视频摘要
    - `3`: 同时进行视频行为挖掘和摘要生成
- **Response Success**:
  ```json
  {
    "msg": "success",
    "code": 0,
    "data": {
      "m_id": "unique_video_id"
    }
  }
  ```
- **Response Error**:
  ```json
  {
    "error": "error_message"
  }
  ```
- **错误码**:
  - `400`: 请求参数错误
  - `500`: 服务器内部错误
- **注意事项**:
  - 视频必须先通过上传接口上传后才能添加
  - `action_type` 必须是 1、2 或 3，其他值将返回错误
  - 如果视频不存在，将返回 "Video not found" 错误
- **处理流程**:
  1. 根据 video_url 检查视频是否存在
  2. 根据 action_type 执行相应的分析操作：
     - 行为挖掘：识别视频中的驾驶行为和交通参与者行为
     - 摘要生成：生成视频内容的文字摘要
  3. 将分析结果存储到 Milvus 数据库
  4. 返回唯一标识符 m_id
- **示例**:
  ```python
  import requests
  
  url = "http://127.0.0.1:30501/vision-analyze/video/add"
  data = {
      "video_url": "http://your-oss-domain/path/to/video.mp4",
      "action_type": 3  # 进行完整分析
  }
  
  response = requests.post(url, data=data)
  print(response.json())
  ```

### 3. 视频行为挖掘
- **URL**: `/vision-analyze/video/mining`
- **Method**: POST
- **描述**: 分析视频中的驾驶行为和交通参与者行为
- **Form Data**:
  - `file_name`: 视频的 OSS URL（从上传接口返回的 video_url）
- **Response Success**:
  ```json
  {
    "msg": "success",
    "code": 0,
    "data": [
      {
        "analysis": "前方车辆突然减速",
        "behaviour": {
          "behaviourId": "B1",
          "behaviourName": "车辆急刹",
          "timeRange": "00:00:11-00:00:12"
        }
      },
      {
        "analysis": "车辆在高速公路上行驶",
        "behaviour": {
          "behaviourId": "B14",
          "behaviourName": "高速路",
          "timeRange": "00:00:00-00:01:30"
        }
      }
    ]
  }
  ```
- **Response Error**:
  ```json
  {
    "error": "error_message"
  }
  ```
- **错误码**:
  - `500`: 服务器内部错误
- **支持的行为类型**:
  - 车辆行为：
    - B1: 车辆急刹
    - B2: 车辆逆行
    - B3: 车辆变道
    - B4: 连续变道
    - B5: 车辆压线
    - B6: 实线变道
    - B7: 车辆碰撞
    - B8: 未开车灯
    - B9: 未打信号灯
  - 其他交通参与者行为：
    - B10: 非机动车乱窜
    - B11: 行人横穿
    - B12: 行人闯红灯
  - 道路环境：
    - B13: 自行车
  - 行驶环境：
    - B14: 高速路
    - B15: 雨天
    - B16: 夜间

### 4. 视频摘要生成
- **URL**: `/vision-analyze/video/summary`
- **Method**: POST
- **描述**: 生成视频内容的文字摘要描述
- **Form Data**:
  - `file_name`: 视频的 OSS URL（从上传接口返回的 video_url）
- **Response Success**:
  ```json
  {
    "msg": "success",
    "code": 0,
    "data": {
      "summary": "这是一段高速公路行车视频。视频中显示一辆汽车在高速公路上正常行驶，期间遇到前方车辆突然减速的情况..."
    }
  }
  ```
- **Response Error**:
  ```json
  {
    "error": "error_message"
  }
  ```
- **错误码**:
  - `500`: 服务器内部错误

### 5. 视频搜索
- **URL**: `/vision-analyze/video/search`
- **Method**: GET
- **描述**: 根据文本搜索相关视频
- **Query Parameters**:
  - `txt`: 搜索文本（可选，仅支持字母数字）
  - `page`: 页码（可选，默认值：1）
  - `page_size`: 每页显示数量（可选，默认值：6）
- **Response Success**:
  ```json
  {
    "msg": "success",
    "code": 0,
    "data": {
      "list": [
        {
          "m_id": "video_id_1",
          "path": "video_url_1",
          "thumbnail_path": "thumbnail_url_1",
          "summary_txt": "视频摘要内容...",
          "tags": ["高速路", "车辆急刹"]
        }
      ],
      "page": 1,
      "page_size": 6
    }
  }
  ```
- **Response Error**:
  ```json
  {
    "error": "Invalid search text"
  }
  ```
- **错误码**:
  - `400`: 请求参数错误（如搜索文本包含非字母数字字符）
  - `500`: 服务器内部错误
- **注意事项**:
  - 搜索文本仅支持字母和数字
  - 返回结果按相关度排序
  - 支持分页查询
- **示例**:
  ```python
  import requests
  
  url = "http://127.0.0.1:30501/vision-analyze/video/search"
  params = {
      "txt": "highway",
      "page": 1,
      "page_size": 10
  }
  
  response = requests.get(url, params=params)
  print(response.json())
  ```
