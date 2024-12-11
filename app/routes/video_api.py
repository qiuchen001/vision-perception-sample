from flask import Blueprint, request
from ..services.video.upload import UploadVideoService
from ..services.video.mining import MiningVideoService
from ..services.video.summary import SummaryVideoService
from ..services.video.add import AddVideoService
from ..services.video.search import SearchVideoService
from ..utils.response import api_handler, api_response, error_response

bp = Blueprint('video', __name__)

@bp.route('upload', methods=['POST'])
@api_handler
def upload_video():
    """
    上传视频文件并处理。
    
    视频文件会被上传到对象存储，同时提取视频帧并存入向量数据库。
    处理过程包括：
    1. 上传视频到OSS
    2. 生成缩略图
    3. 提取视频帧
    4. 生成帧向量并存入Milvus
    5. 添加视频信息到数据库
    """
    if 'video' not in request.files:
        raise ValueError("No video file provided")

    video_file = request.files['video']
    
    if not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
        raise ValueError("Invalid file type")

    video_service = UploadVideoService()
    result = video_service.upload(video_file)

    return api_response(result)

@bp.route('mining', methods=['POST'])
@api_handler
def mining_video():
    video_url = request.form.get('file_name')
    if not video_url:
        raise ValueError("Missing file_name parameter")

    video_service = MiningVideoService()
    mining_result_new = video_service.mining(video_url)

    return api_response(mining_result_new)

@bp.route('summary', methods=['POST'])
@api_handler
def summary_video():
    video_url = request.form.get('file_name')
    if not video_url:
        raise ValueError("Missing file_name parameter")

    video_service = SummaryVideoService()
    mining_content_json = video_service.summary(video_url)

    return api_response(mining_content_json)

@bp.route('add', methods=['POST'])
@api_handler
def add_video():
    video_url = request.form.get('video_url')
    action_type = request.form.get('action_type')

    if not video_url:
        raise ValueError("Missing video_url parameter")
    if not action_type:
        raise ValueError("Missing action_type parameter")

    try:
        action_type = int(action_type)
        if action_type not in [1, 2, 3]:
            raise ValueError("Invalid action_type value. Must be 1, 2, or 3")
    except ValueError:
        raise ValueError("action_type must be an integer")

    video_service = AddVideoService()
    m_id = video_service.add(video_url, action_type)

    return api_response({"m_id": m_id})

@bp.route('search', methods=['GET'])
@api_handler
def search_video():
    txt = request.args.get('txt')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=6, type=int)

    if txt and not txt.isalnum():
        raise ValueError("Invalid search text")
    if page < 1:
        raise ValueError("Page number must be greater than 0")
    if page_size < 1:
        raise ValueError("Page size must be greater than 0")

    video_service = SearchVideoService()
    video_list = video_service.search(txt, page, page_size)

    return api_response({
        "list": video_list,
        "page": page,
        "page_size": page_size
    })