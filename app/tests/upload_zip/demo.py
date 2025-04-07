import unittest
import uuid
import json
import requests
import requests_mock
import os
import zipfile
from pathlib import Path
from unittest.mock import patch


class CommonResult:
    def __init__(self, success, message, data=None):
        self.success = success
        self.message = message
        self.data = data


class CollectDataController:
    def __init__(self):
        # self.storage_uri = "http://storage-manager-service:8080"
        # self.storage_uri = "http://10.66.12.37:30112"
        self.storage_uri = "http://10.66.12.37:30112"
        # self.storage_uri = "http://127.0.0.1:8010"

    def upload_zip(self, bytes_data, file_name, task_id):
        try:
            url = f"{self.storage_uri}/filestore/rawdata"
            params = {
                "filename": file_name,
                "taskId": task_id
            }
            headers = {"Content-Type": "application/octet-stream"}

            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=bytes_data
            )

            return response

            # if response.status_code != 200:
            #     return CommonResult(
            #         False,
            #         f"Storage service returned status code: {response.status_code}",
            #         response.json() if response.text else None
            #     )
            #
            # response_json = response.json()
            # if response_json.get("result") != "success":
            #     return CommonResult(
            #         False,
            #         response_json.get("msg", "Unknown error"),
            #         response_json
            #     )
            #
            # return CommonResult(
            #     True,
            #     response_json.get("msg", "Upload successful"),
            #     response_json
            # )

        except Exception as e:
            return CommonResult(False, str(e), None)


# class TestCollectDataController():
#     # @classmethod
#     # def setUpClass(cls):
#     #     """测试类开始前创建测试zip文件"""
#     #     cls.test_zip_path = create_test_zip()
#     #
#     # def setUp(self):
#     #     self.controller = CollectDataController()
#     #     # self.controller.storage_uri = "http://localhost:8089"
#     #     # self.controller.storage_uri = "http://10.66.12.37:30112"
#     #     self.controller.storage_uri = "http://127.0.0.1:8081"
#
#     def test_upload_zip_success(self):
#         with requests_mock.Mocker() as m:
#
#
#             file_name = "GWM-LANSHAN/NAS10S_2022-01-01/NAS10S_20220101_084465_01.zip"
#             task_id = str(uuid.uuid4())
#
#             # 读取真实的zip文件
#             with open(self.test_zip_path, "rb") as f:
#                 zip_bytes = f.read()
#
#             # 执行测试
#             result = self.controller.upload_zip(zip_bytes, file_name, task_id)
#
#             print(result)

if __name__ == "__main__":
    # zip_path = "C:/Users/zhangchenchen/Desktop/tmp/NAS10S_20220101_084465_01.zip"
    zip_path = r"C:\Users\zhangchenchen\Desktop\tmp\NAS10S_20220101_084465_01.zip"

    # file_name = "GWM-LANSHAN/NAS10S_2022-01-01/NAS10S_20220101_084465_01.zip"
    # file_name = "NAS10S_20220101_084465_01.zip"
    file_name = "GWM-LANSHAN/NAS10S_2022-01-01/NAS10S_20220101_084465_01.zip"
    task_id = str(uuid.uuid4())

    # 读取真实的zip文件
    with open(zip_path, "rb") as f:
        zip_bytes = f.read()

    controller = CollectDataController()
    controller.upload_zip(zip_bytes, file_name, task_id)