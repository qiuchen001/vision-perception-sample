from flask import Blueprint, jsonify, request
from ..services.video_service import VideoService
from ..utils.logger import logger


bp = Blueprint('video', __name__)

@bp.route('/get', methods=['GET'])
def get_users():
    logger.info("Fetching all users via API")
    video_service = VideoService()
    videos = video_service.get_all_videos()
    # return jsonify([{'id': video['id'], 'username': video['username'], 'email': video['email']} for video in videos])
    return jsonify([])

@bp.route('upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']

    video_service = VideoService()
    video_oss_url = video_service.upload(video_file)

    # video_oss_url = uploadVideoService(video_file)

    print(video_oss_url)

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
        # mining_result = mining_video_handler(video_url)
        # js = json.loads(mining_result)
        # content = js['choices'][0]['message']['content']
        # mining_json = parse_json_string(content)
        # mining_result_new = format_mining_result(mining_json, video_url)
        video_service = VideoService()
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