import time
import os
from get_info import *
import requests
from des import des

def check_in(username: str, password: str, timeout: int = 10):
    def vacation_enable(token, timeout):
        headers = {
            "fighter-auth-token": token
        }
        url = 'https://of.swu.edu.cn/gateway/fighter-baida/api/flow-ext/start-process-instance-by-key'
        params = {'processDefinitionKey': 'XSQJXJ'}
        response = requests.post(headers=headers, params=params, json={}, url=url, timeout=timeout)
        if response.json()["code"] == 200 or response.json()["code"] == 1100:
            return 0
        else:
            return 1

    def checkin_post(token, timeout):
        try:
            transition_today = get_transition_today(token)
            if transition_today is None:
                return None
            formid = transition_today["formId"]
            id = transition_today["id"]
            headers = {"fighter-auth-token": token, "Content-Type": "application/json;charset=UTF-8"}
            url = "https://of.swu.edu.cn/gateway/fighter-baida/api/form-instance/save"
            params = {"formId": formid, "isSubmitProcess": False}
            dormitory = get_dormitory(token, timeout)["data"]["columList"]
            payload = {
                "id": id,
                "formId": formid,
                "tsrq": time.strftime("%Y-%m-%d"),
                "xh": get_student_id(token),
                "qdsj": ["21:00", "23:30"],
                "qsqddd": dormitory[1]["value"],
                "qdbj": dormitory[2]["value"],
                "qddz": {
                    "latitude": dormitory[0]["latitude"],
                    "longitude": dormitory[0]["longitude"],
                    "address": dormitory[1]["value"],
                    "netType": "wifi",
                    "operatorType": "unknown",
                    "imei": "imei",
                    "time": int(time.time() * 1000),
                    "provider": "lbs",
                    "isFromMock": False,
                    "isGpsEnabled": True,
                    "isWifiEnabled": True,
                    "isMobileEnabled": False,
                    "isOffset": True,
                    "cityAdCode": "023",
                    "districtAdCode": "500109",
                    "isArea": True,
                    "tip": "当前在签到范围内"
                }
            }
            response = requests.post(url, headers=headers, params=params, data=json.dumps(payload), timeout=timeout).json()["data"]
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return 4

    if not verify(username, password, timeout):
        return 3
    token = get_token(username, password, timeout)
    if vacation_enable(token, timeout):
        return 5
    transition_today =  get_transition_today(token, timeout)
    if not transition_today:
        return 0
    if transition_today["qdzt"] == "已签到":
        return 2
    post_result = checkin_post(token, timeout)
    if post_result == 4:
        return 4
    return 1


if __name__ == "__main__":
    print("开始执行签到...")
    user = os.getenv("SWU_USERNAME", "").strip()
    pwd = os.getenv("SWU_PASSWORD", "").strip()

    if not user or not pwd:
        print("缺少账号密码，请设置 SWU_USERNAME/SWU_PASSWORD。")
        raise SystemExit(1)

    print("已从环境变量读取账号信息。")

    result = check_in(user, pwd)
    message_map = {
        0: "今日暂无签到任务。",
        1: "签到成功。",
        2: "今日已签到，无需重复操作。",
        3: "账号或密码验证失败，请检查后重试。",
        4: "连接错误或请求超时，请稍后重试。",
        5: "请假中，请检查是否有打卡任务。"
    }
    print(message_map.get(result))
