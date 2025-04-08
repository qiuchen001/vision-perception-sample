# -*- coding: utf-8 -*-
import pymongo
import requests
import json
import os
from gridfs import GridFS


class MongoFileStore(GridFS):
    
    def __init__(self, project_name, collection_name, appkey=None, k8s_master_host="10.66.12.37"):
        self.collection_name=collection_name
        self.project_name=project_name
        env = os.getenv("BDP_ENV")
        if env == "dev": # 在k8s内部访问
            validation_service_url = "http://storage-manager-service:8080/mongodb/collections"
            self.storage_url = "http://storage-manager-service:8080/"

        elif env == "prod": # 在k8s内部访问
            validation_service_url = "http://storage-manager-service:8080/mongodb/collections"
            self.storage_url = "http://storage-manager-service:8080/"

        else: # 没有env，则视为在k8s外部访问，仅可访问default环境
            validation_service_url = "http://" + k8s_master_host + ":30080/default/mongodbsvc/mongodb/collections"
            self.storage_url = "http://" + k8s_master_host + ":30080/default/mongodbsvc/"
            #self.storage_url = "http://localhost:8010/"

        if collection_name is None or collection_name.strip() == '':
            raise RuntimeError("collection_name must not be empty!")
        if project_name is None or project_name.strip() == '':
            self.project_name = "public"
        try:
            headers = {'content-type': 'application/json'}
            url = validation_service_url + "/{0}?project-name={1}".format(collection_name, project_name)
            response = requests.get(url, headers=headers)
            if response is None or response.status_code != 200:
                raise RuntimeError('collection not find"' + collection_name + '" not found.')
            collection_info = json.loads(response.content)["collection"]
            authed = True
            if collection_info["enableAuthorization"] == 1:
                authedAppkeys = collection_info["authedAppKeys"]
                if authedAppkeys is not None and authedAppkeys != '':
                    if appkey is None or appkey not in authedAppkeys.split(","):
                        authed = False
                else:
                    authed = False
            if not authed:
                if appkey is None:
                    raise RuntimeError('Collection info"' + project_name + "-" + collection_name + '" authorization denied with empty appkey, please contact ' + collection_info["owners"])
                else:
                    raise RuntimeError(
                        'Collection info"' + project_name + "-" + collection_name + '" authorization denied with appkey "' + appkey + '", please contact ' +
                        collection_info["owners"])
            if collection_info["storeType"] != 'file_store':
                raise RuntimeError("This collection is only used for storing files.")
        except:
            raise RuntimeError("Could not validate collection info: " + project_name + "-" + collection_name)


    def put(self, data, filename, **attr):
        # print(self.storage_url)
        headers = {'content-type': 'application/octet-stream'}
        params={'filename':filename}
        response = requests.post(self.storage_url+"filestore/"+self.collection_name,data=data,params=params,headers=headers)
        return response

    def get(self, filename):
        headers = {'content-type': 'application/json'}
        params={'filename':filename}
        response=requests.get(self.storage_url+"filestore/"+self.collection_name,params=params,headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise RuntimeError("file download failed！response："+response.content)

# import io

# source_collection = MongoFileStore("public", "source_data")
# input_collection = MongoFileStore("public", "trajectory_xosc")
# file1 = input_collection.get('23520c3b-c7ff-4bc6-9437-bcf6fab6c309.judge')
# result=source_collection.put(file1.decode('utf-8'),"testFile.csv")
# print("Finish")
# # with open('test.csv', 'wb') as f:
#         f.write(result)
#         print("Finish")
