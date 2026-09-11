from datetime import datetime
from getpass import getpass
import json
import os
import time

import requests

from .get_info import get_dormitory, get_student_id, get_transition_today, get_token

STATUS_MESSAGES = {
    0: "今日无签到记录",
    1: "签到成功",
    2: "已签到",
    3: "登录失败",
    4: "网络错误或数据异常",
    5: "请假期间无需签到",
}

# 终态不重试：成功 / 已签到 / 请假
# 其余（无记录、登录失败、网络异常）可能是抖动，打满次数才算失败
RETRYABLE_STATUS = {0, 3, 4}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 8


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _check_vacation_enabled(token: str, timeout: int) -> bool:
    """检查是否在请假期间"""
    headers = {"fighter-auth-token": token}
    url = "https://of.swu.edu.cn/gateway/fighter-baida/api/xsqjxj/listSelfLeaveData?pageNum=1&pageSize=10"
    
    try:
        response = requests.get(url=url, headers=headers, timeout=timeout)
        data = response.json().get("data", {})
        records = data.get("records", [])
        
        if not records:
            return False
        
        latest = records[0]
        if latest.get("lcztmc") != "已同意":
            return False
        
        now = datetime.now()
        start = datetime.strptime(latest["kssj"], "%Y-%m-%d %H:%M")
        end = datetime.strptime(latest["jssj"], "%Y-%m-%d %H:%M")
        
        return start <= now <= end
    except (requests.exceptions.RequestException, KeyError, ValueError):
        return False


def _parse_dormitory_data(dormitory_list: list) -> tuple[dict, str, str]:
    """
    从 getDormitory 返回的 columnList 解析签到数据
    返回: (位置信息, 宿舍楼名, 房间号)
    """
    location = None
    building = None
    room = None
    
    for item in dormitory_list:
        prop = item.get("prop", "")
        if prop == "qddz":
            location = {
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude")
            }
        elif prop == "qsqddd":
            building = item.get("value")
        elif prop == "qdbj":
            room = item.get("value")
    
    if not all([location, building, room]):
        raise ValueError("宿舍信息不完整")
    
    return location, building, room


def _submit_checkin(token: str, timeout: int) -> int:
    """
    执行签到请求
    返回: 1=成功, 4=网络错误, None=无今日记录
    """
    try:
        transition = get_transition_today(token, timeout)
        if transition is None:
            return None
        
        form_id = transition["formId"]
        record_id = transition["id"]
        
        # 获取宿舍信息
        dorm_response = get_dormitory(token, timeout)
        column_list = dorm_response.get("data", {}).get("columnList", [])
        location, building, room = _parse_dormitory_data(column_list)
        
        headers = {
            "fighter-auth-token": token,
            "Content-Type": "application/json;charset=UTF-8"
        }
        url = "https://of.swu.edu.cn/gateway/fighter-baida/api/form-instance/save"
        params = {"formId": form_id, "isSubmitProcess": False}
        
        payload = {
            "id": record_id,
            "formId": form_id,
            "tsrq": time.strftime("%Y-%m-%d"),
            "xh": get_student_id(token, timeout),
            "qdsj": ["21:00", "23:30"],
            "qsqddd": building,
            "qdbj": room,
            "qddz": {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "address": building,
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
        
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=json.dumps(payload),
            timeout=timeout
        )
        response.raise_for_status()
        return 1
        
    except requests.exceptions.RequestException:
        return 4
    except (KeyError, ValueError, TypeError):
        return 4


def check_in(username: str, password: str, timeout: int = 10) -> int:
    """
    执行一次宿舍签到。

    返回值:
        0: 今日无签到记录
        1: 签到成功
        2: 已签到
        3: 登录失败
        4: 网络错误或数据异常
        5: 请假期间无需签到
    """
    try:
        token = get_token(username, password, timeout)
        if not token:
            return 3

        if _check_vacation_enabled(token, timeout):
            return 5

        transition = get_transition_today(token, timeout)
        if not transition:
            return 0

        if transition.get("qdzt") == "已签到":
            return 2

        result = _submit_checkin(token, timeout)
        if result is None:
            return 0

        return result
    except (KeyboardInterrupt, SystemExit):
        raise
    except (requests.exceptions.RequestException, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return 4
    except Exception:
        return 4


def check_in_with_retry(
    username: str,
    password: str,
    timeout: int = 10,
    max_attempts: int | None = None,
    retry_delay: int | None = None,
) -> int:
    """
    执行签到，瞬时失败自动重试。

    可通过环境变量覆盖：
        SWUDK_MAX_ATTEMPTS  总尝试次数，默认 3
        SWUDK_RETRY_DELAY   首次重试等待秒数，之后指数退避，默认 8
    """
    attempts = max_attempts or _env_int("SWUDK_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS)
    delay = retry_delay or _env_int("SWUDK_RETRY_DELAY", DEFAULT_RETRY_DELAY)
    last_result = 4

    for attempt in range(1, attempts + 1):
        last_result = check_in(username, password, timeout)
        if last_result not in RETRYABLE_STATUS or attempt >= attempts:
            return last_result

        wait = delay * (2 ** (attempt - 1))
        reason = STATUS_MESSAGES.get(last_result, "未知状态")
        print(f"第 {attempt}/{attempts} 次失败（{reason}），{wait} 秒后重试")
        time.sleep(wait)

    return last_result


def main() -> int:
    username = os.getenv("SWUDK_USERNAME") or input("校园网账号：").strip()
    password = os.getenv("SWUDK_PASSWORD") or getpass("校园网密码：")
    result = check_in_with_retry(username, password, 10)
    print(f"[{result}] {STATUS_MESSAGES.get(result, '未知状态')}")
    return 0 if result in {1, 2} else 1


if __name__ == "__main__":
    raise SystemExit(main())