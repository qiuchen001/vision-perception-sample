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
- **Flask**：Web 框架��用于构建 API 和处理请求。
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
- **Form Data**:
  - `video`: 视频文件

### 2. 添加视频
- **URL**: `/vision-analyze/video/add`
- **Method**: POST
- **Form Data**:
  - `video_url`: 视频 URL
  - `action
