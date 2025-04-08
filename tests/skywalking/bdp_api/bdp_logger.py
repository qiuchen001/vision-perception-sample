# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import threading
import json
import os
from bdp_api.kafka_client import KafkaProducer
import logging
from skywalking.trace.context import get_context
import urllib3
from urllib.parse import urljoin

g_http_connection_pool = urllib3.PoolManager()


class BDPLogger:
    def __init__(self):
        self.__kafkaProducer = KafkaProducer("public", "platform-logs")
        self.__job_name = os.getenv("JOB_NAME")
        self.__project_name = os.getenv("PROJECT_NAME")
        self.__logger = logging.getLogger('bdpLogger')
        self.__logger.setLevel(logging.DEBUG)
        env = os.getenv("BDP_ENV")
        if env == "dev":  # 在k8s内部访问
            self.scene_service_url = "http://ad-scene-manager-service:8080/"
        elif env == "prod":  # 在k8s内部访问
            self.scene_service_url = "http://ad-scene-manager-service:8080/"
        else:
            self.scene_service_url = "http://10.66.12.37:30080/default/adscene/"

    def update_process_status(self, process_status, fts=None):
        context = get_context()
        trace_id = context.segment.related_traces[0].value

        update_url = os.getenv("LOG_SERVICE_ADDR")
        if update_url is None or update_url.strip() == '':
            update_url = urljoin(self.scene_service_url, "logs")

        if fts is not None:
            body_json = {'trace_id': trace_id, 'job_status': process_status, 'finish_date': fts}
        else:
            body_json = {'trace_id': trace_id, 'job_status': process_status}
        response = g_http_connection_pool.request('PATCH', update_url, headers={'Accept': 'application/json',
                                                                                'Content-Type': 'application/json'},
                                                  body=json.dumps(body_json))
        if response is None or response.status != 200:
            self.__logger.error("update process trace status failed!  ")
        # else:
        #     self.__logger.info("update process trace status success!")

    def info(self, msg):
        self.__logger.info(self.__project_name + "-" + self.__job_name + " - " + msg)
        kafka_data = json.dumps({'projectName': self.__project_name, 'jobName': self.__job_name,
                                 'msg': self.__make_message_header('INFO') + msg})
        self.__kafkaProducer.produce(kafka_data)

    def error(self, msg):
        self.__logger.error(self.__project_name + "-" + self.__job_name + " - " + msg)
        self.update_process_status('error')
        kafka_data = json.dumps({'projectName': self.__project_name, 'jobName': self.__job_name,
                                 'msg': self.__make_message_header('ERROR') + msg})
        self.__kafkaProducer.produce(kafka_data)

    def warn(self, msg):
        self.__logger.warn(self.__project_name + "-" + self.__job_name + " - " + msg)
        self.update_process_status('warn')
        kafka_data = json.dumps({'projectName': self.__project_name, 'jobName': self.__job_name,
                                 'msg': self.__make_message_header('WARN') + msg})
        self.__kafkaProducer.produce(kafka_data)

    def finish(self, msg):
        self.__logger.info(self.__project_name + "-" + self.__job_name + " - " + msg)
        tn = datetime.utcnow() + timedelta(hours=8)
        ts = tn.strftime('%Y-%m-%d %H:%M:%S')
        self.update_process_status('finish', ts)

    def debug(self, msg):
        self.__logger.debug(self.__project_name + "-" + self.__job_name + " - " + msg)
        kafka_data = json.dumps({'projectName': self.__project_name, 'jobName': self.__job_name,
                                 'msg': self.__make_message_header('DEBUG') + msg})
        self.__kafkaProducer.produce(kafka_data)

    def __make_message_header(self, tag):
        ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f ')[:-4]
        thread_info = '[' + threading.currentThread().name + '-' + str(threading.currentThread().ident) + ']'
        return ts + ' ' + thread_info + ' ' + tag + '  '


logger = BDPLogger()
