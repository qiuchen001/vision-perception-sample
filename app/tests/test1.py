import requests
import json
import time





def getSign():
    appId = "7f4ad24546a44a9fa3ff9891c75d5d9b"
    response = requests.get(f"https://api.gwm-adas.com/sign_server/auth/getSign?appId={appId}")
    js = response.json()
    # print(f"签名结果:{js}")

    return js['obj']


def get_trigger_data(appId, signature, timestamp):
    data = {
        "start_time": "2024-10-01 12:00:00",
        "end_time": "2024-12-11 12:30:00",
        "tags": "60",
        # "vin": "123,456,789"
    }
    headers = {
        "Content-Type": "application/json",
        "appId": appId,
        "signature": signature,
        "timestamp": str(timestamp)  # 当前时间戳，转换为字符串
    }
    response = requests.post("https://api.gwm-adas.com/get_trigger_server/api/getTriggerData", data=json.dumps(data),
                             headers=headers)
    js = response.json()
    print(f"合规数据查询参数:{data}")
    print(f"合规数据查询结果:{js}")
    return js['obj']


if __name__ == '__main__':
    sign_res = getSign()
    appId = sign_res.get("appId")
    signature = sign_res.get("signature")
    timestamp = sign_res.get("timestamp")

    time.sleep(1)

    trigger_data_res = get_trigger_data(appId, signature, timestamp)
