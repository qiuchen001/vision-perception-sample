from app.dao.video_dao import VideoDAO
from app.utils.logger import logger
from app.utils.common import *
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
            return upload_thumbnail_to_oss(filename, video_file_path)
        finally:
            os.remove(video_file_path)
            logger.debug(f"Deleted temporary file: {video_file_path}")


# uploadVideoService = UploadVideoService()