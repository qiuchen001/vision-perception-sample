from flask import Blueprint, request, Response
import requests

bp = Blueprint('video_proxy', __name__)


@bp.route('/video_proxy')
def proxy_video():
    """视频代理路由"""
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL parameter", 400

    try:
        # 转发请求到实际的视频URL
        resp = requests.get(video_url, stream=True)

        # 创建响应
        response = Response(
            resp.iter_content(chunk_size=10 * 1024),
            content_type=resp.headers.get('content-type', 'video/mp4')
        )

        # 设置必要的响应头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Accept-Ranges'] = 'bytes'

        return response
    except Exception as e:
        return f"Error proxying video: {str(e)}", 500
