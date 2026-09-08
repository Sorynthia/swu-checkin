from datetime import datetime
from getpass import getpass
import json
import os
import time

import requests

from get_info import get_dormitory, get_student_id, get_transition_today
from verify import get_token



def check_in(username: str, password: str, timeout: int = 10) ->int:
    def vacation_enable(token, timeout):
        headers = {
            "fighter-auth-token": token
        }
        url = "https://of.swu.edu.cn/gateway/fighter-baida/api/xsqjxj/listSelfLeaveData?pageNum=1&pageSize=10"
        response = requests.get(url=url, headers=headers, timeout=timeout)
        #print(response.json())
        if not response.json()["data"]["records"]:
            return False
        is_agree = response.json()["data"]["records"][0]["lcztmc"] == "已同意"
        if not is_agree:
            return False
        now_time = datetime.now()
        qjxx = response.json()["data"]["records"][0]
        start_time = datetime.strptime(qjxx["kssj"], "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(qjxx["jssj"], "%Y-%m-%d %H:%M")
        if start_time <= now_time <= end_time:
            return True
        return False

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
            dormitory = get_dormitory(token, timeout)["data"]["columnList"]
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
    token = get_token(username, password, timeout)
    if token == "":
        return 3
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
    username = os.getenv("SWUDK_USERNAME") or input("校园网账号：").strip()
    password = os.getenv("SWUDK_PASSWORD") or getpass("校园网密码：")
    print(check_in(username, password, 10))
