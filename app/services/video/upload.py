from app.dao.video_dao import VideoDAO
from app.utils.logger import logger
from app.utils.common import *
from app.utils.embedding import *
from app.utils.minio_uploader import MinioFileUploader
from werkzeug.utils import secure_filename
import os


class UploadVideoService:
    def __init__(self):
        self.video_dao = VideoDAO()
        self.minioFileUploader = MinioFileUploader()

    def upload(self, video_file):
        filename = secure_filename(video_file.filename)
        video_file_path = os.path.join('/tmp', filename)
        video_file.save(video_file_path)

        try:
            video_oss_url = upload_thumbnail_to_oss(filename, video_file_path)
            thumbnail_oss_url = self.minioFileUploader.generate_video_thumbnail_url(video_oss_url)
        finally:
            os.remove(video_file_path)
            logger.debug(f"Deleted temporary file: {video_file_path}")

        if not self.video_dao.check_url_exists(video_oss_url):
            embedding = embed_fn("")
            self.video_dao.insert_url(video_oss_url, embedding, thumbnail_oss_url)

        return video_oss_url