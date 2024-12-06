from flask import Flask
from logging.config import dictConfig
import logging_config
from milvus_client import MilvusClientWrapper
import os
from dotenv import load_dotenv
load_dotenv()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_name)

    # db.init_app(app)

    # 配置日志
    dictConfig(logging_config.LOGGING_CONFIG)

    # 初始化 Milvus 客户端
    SERVER_HOST = os.getenv("DB_NAME")
    app.config['SERVER_HOST'] = SERVER_HOST
    app.config['MILVUS_CLIENT'] = MilvusClientWrapper(uri=f"http://{SERVER_HOST}:19530", db_name="video_db")

    from .routes import main, video_api
    app.register_blueprint(main.bp)
    app.register_blueprint(video_api.bp, url_prefix='/vision-analyze/video')

    return app
