from flask import Blueprint, send_file, abort, current_app, Response
import requests
from urllib.parse import unquote
import os

bp = Blueprint('video_proxy', __name__)

@bp.route('/proxy/<path:video_path>')
def video_proxy(video_path):
    try:
        # 解码URL
        video_url = unquote(video_path)
        if not video_url.startswith('http'):
            video_url = f'http://{video_url}'
            
        current_app.logger.info(f"Proxying video: {video_url}")
            
        # 获取视频内容
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            current_app.logger.error(f"Failed to fetch video: {response.status_code}")
            return abort(404)
            
        # 返回视频流
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
                
        return Response(
            generate(),
            content_type=response.headers.get('content-type', 'video/mp4'),
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Length': response.headers.get('content-length'),
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Video proxy error: {str(e)}")
        return abort(500)
