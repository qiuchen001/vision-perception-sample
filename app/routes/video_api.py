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


@bp.route('search', methods=['POST'])
@api_handler
def search_video():
    """
    搜索视频。支持文本搜索和图片搜索。
    
    请求方式：POST
    
    参数：
        txt: 搜索文本（可选）
        image: 图片文件（可选）
        image_url: 图片URL（可选）
        page: 页码（默认1）
        page_size: 每页数量（默认6）
        
    注意：
        - txt、image、image_url 三者必须提供其中之一
        - image 和 image_url 不能同时提供
    """
    page = request.form.get('page', default=1, type=int)
    page_size = request.form.get('page_size', default=6, type=int)

    if page < 1:
        raise ValueError("Page number must be greater than 0")
    if page_size < 1:
        raise ValueError("Page size must be greater than 0")

    video_service = SearchVideoService()

    # 获取搜索参数
    txt = request.form.get('txt')
    image_file = request.files.get('image')
    image_url = request.form.get('image_url')

    # 参数验证
    if not any([txt, image_file, image_url]):
        raise ValueError("Must provide either txt, image file or image URL")

    if sum(bool(x) for x in [txt, image_file, image_url]) > 1:
        raise ValueError("Can only provide one of: txt, image file, image URL")

    # 根据提供的参数类型执行相应的搜索
    if txt:
        video_list = video_service.search_by_text(txt, page, page_size)
    else:
        video_list = video_service.search_by_image(
            image_file=image_file,
            image_url=image_url,
            page=page,
            page_size=page_size
        )

    return api_response({
        "list": video_list,
        "page": page,
        "page_size": page_size
    })
