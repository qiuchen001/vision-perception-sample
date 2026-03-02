import urllib.parse
import urllib3
import json


http_connection_pool = urllib3.PoolManager()


def get_tags(scene_id):
    tagPaths, tagIds = [], []

    params = {
        "businessType": "scene",
        "businessId": scene_id
    }
    query_string = urllib.parse.urlencode(params)
    url_with_params = f"http://10.66.12.37:31557/biz-tags?{query_string}"
    res = http_connection_pool.request("GET", url_with_params)
    if res.status == 200:
        tags_info = json.loads(res.data.decode())
        if tags_info["data"] is not None and tags_info["data"]["list"] is not None:
            tag_list = tags_info["data"]["list"]
            for item in tag_list:
                tagPaths.append(item['tagPath'])
                tagIds.append(item['tagId'])

    return tagPaths, tagIds

businessId="789174d0-45df-4d64-8ea9-b3faa5236df3"
tagPaths, tagIds = get_tags(businessId)
print(tagPaths)
print(tagIds)