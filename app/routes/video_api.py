from flask import Blueprint, jsonify, request
from ..services.video.upload import UploadVideoService
from ..services.video.mining import MiningVideoService
from ..services.video.summary import SummaryVideoService
from ..services.video.add import AddVideoService
from ..services.video.search import SearchVideoService
from ..utils.logger import logger
from app.dao.video_dao import VideoDAO


bp = Blueprint('video', __name__)

@bp.route('upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']

    video_service = UploadVideoService()
    video_oss_url = video_service.upload(video_file)

    response = {
        "msg": "success",
        "code": 0,
        "data": {
            "file_name": video_oss_url,
            "video_url": video_oss_url,
        }
    }

    return jsonify(response), 200


@bp.route('mining', methods=['POST'])
def mining_video():
    video_url = request.form.get('file_name')
    try:
        video_service = MiningVideoService()
        mining_result_new = video_service.mining(video_url)

        response = {
            "msg": "success",
            "code": 0,
            "data": mining_result_new
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in mining video: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('summary', methods=['POST'])
def summary_video():
    video_url = request.form.get('file_name')
    try:
        video_service = SummaryVideoService()
        mining_content_json = video_service.summary(video_url)

        response = {
            "msg": "success",
            "code": 0,
            "data": mining_content_json
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in summary video: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('add', methods=['POST'])
def add_video():
    video_url = request.form.get('video_url')
    action_type = request.form.get('action_type') # 1. 挖掘 2. 提取摘要 3. 挖掘及提取摘要

    try:
        video_service = AddVideoService()
        m_id = video_service.add(video_url, int(action_type))

        response = {
            "msg": "success",
            "code": 0,
            "data": {
                "m_id": m_id
            }
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in add video: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('search', methods=['GET'])
def search_video():
    txt = request.args.get('txt')  # 使用 request.args.get 获取 GET 请求参数
    page = request.args.get('page', default=1, type=int)  # 获取分页参数，默认第一页
    page_size = request.args.get('page_size', default=6, type=int)  # 每页显示数量，默认6条

    try:
        video_service = SearchVideoService()
        video_list = video_service.search(txt, page, page_size)  # 传递分页参数到服务层

        response = {
            "msg": "success",
            "code": 0,
            "data": {
                "list": video_list,
                "page": page,
                "page_size": page_size
            }
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in search video: {e}")
        return jsonify({"error": str(e)}), 500