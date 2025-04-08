# -*- coding: utf-8 -*-
# import requests
import json
import os
import urllib3
import requests
from concurrent.futures import ThreadPoolExecutor

class KafkaProducer:
    def __init__(self, project_name, topic_name, max_workers=8, appWriteKey=None, k8s_master_host="10.66.12.37"):
        env = os.getenv("BDP_ENV")
        self.__httpPool = urllib3.PoolManager()
        self.__write_auth = True
        self.__project_name = project_name
        self.__topic_name = topic_name
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.__header = {'Content-Type': 'application/json'}
        if env == "dev": # 在k8s内部访问
            validation_service_url = "http://storage-manager-service:8080/kafka/topics"
            self.__mq_url = "http://storage-manager-service:8080/mq"
        elif env == "prod": # 在k8s内部访问
            validation_service_url = "http://storage-manager-service:8080/kafka/topics"
            self.__mq_url = "http://storage-manager-service:8080/mq"
        else: # 没有env，则视为在k8s外部访问，仅可访问default环境
            storage_manager_service = os.getenv("STORAGE_MANAGER_SERVICE")
            if storage_manager_service is None or storage_manager_service.strip() == '':
                storage_manager_service = "http://" + k8s_master_host + ":30080"
            validation_service_url = storage_manager_service + "/kafka/topics"
            self.__mq_url = storage_manager_service + "/mq"

        if topic_name is None or topic_name.strip() == '':
            raise RuntimeError("topic name must not be empty!")
        headers = {'content-type': 'application/json'}
        url = validation_service_url + "/{0}?project-name={1}".format(topic_name,project_name)
        response = requests.get(url, headers=headers)
        if response is None or response.status_code != 200:
            raise RuntimeError('topic not find"' + project_name + '-' + topic_name + '" not found.')
        topic_info = json.loads(response.content)["topic"]
        self.__write_auth = True
        if topic_info["enableAuthorization"] == 1:
            authedWriteAppKeys = topic_info["authedWriteAppKeys"]
            if authedWriteAppKeys is not None and authedWriteAppKeys != '':
                if appWriteKey is None or appWriteKey not in authedWriteAppKeys.split(","):
                    self.__write_auth  = False
            else:
                self.__write_auth = False
            if not self.__write_auth:
                if appWriteKey is None:
                    raise RuntimeError('Kafka topic authorization failed, topic name:"' + project_name + '-' + topic_name + '", empty appkey, please contact ' + topic_info["owners"])
                else:
                    raise RuntimeError(
                        'Kafka topic authorization failed, topic name:"' + project_name + '-' + topic_name + '", appkey:"' + appWriteKey + '", please contact ' +
                        topic_info["owners"])


    def __produce(self, req):
        url = self.__mq_url + "/" + self.__topic_name
        res = self.__httpPool.request('POST', url, headers=self.__header, body=req)
        return res.data

    def produce(self, value):
        if self.__write_auth:
            req = json.dumps({'msg': value, 'projectName': self.__project_name})
            t = self.__executor.submit(self.__produce, (req))
        else:
            raise RuntimeError("ERROR: permission denied")


# if __name__ == "__main__":
#     pool = urllib3.PoolManager()
#     url = "http://10.66.12.37:30080/default/kafkasvc/mq/public/test"
#     res = pool.request('POST', url, headers={'Content-Type': 'application/json'}, body=json.dumps({'msg': 'test'}))
#     print(res.data)
#
#     # begin = time.time()
#     # for i in range(1000):
#     #     a = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({'msg': 'test'}))
#     # print('requests time used: ' + str(time.time() - begin))
#     #
#     # begin = time.time()
#     # for i in range(1000):
#     #     pool.request('POST', url, headers={'Content-Type': 'application/json'}, body=json.dumps({'msg': 'test'}))
#     # print('urllib3 time used: ' + str(time.time() - begin))