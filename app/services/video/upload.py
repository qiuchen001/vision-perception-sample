from app.dao.video_dao import VideoDAO
from app.utils.logger import logger
from app.utils.common import *
from app.utils.embedding import *
from werkzeug.utils import secure_filename
import os


class UploadVideoService:
    def __init__(self):
        self.video_dao = VideoDAO()

    def upload(self, video_file):
        filename = secure_filename(video_file.filename)
        video_file_path = os.path.join('/tmp', filename)
        video_file.save(video_file_path)

        try:
            video_oss_url = upload_thumbnail_to_oss(filename, video_file_path)
        finally:
            os.remove(video_file_path)
            logger.debug(f"Deleted temporary file: {video_file_path}")

        if not self.video_dao.check_url_exists(video_oss_url):
            embedding = embed_fn("")
            self.video_dao.insert_url(video_oss_url, embedding)

        return video_oss_url