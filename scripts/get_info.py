import json
import requests
import urllib.parse
from des import des
from verify import verify

def get_token(username: str, password: str, timeout=10):
    def transform(ticket):
        ST = urllib.parse.unquote(ticket)
        ticket = urllib.parse.unquote(ticket).split("-")
        str1 = ""
        str2 = ""
        for i in ticket[1]:
            str1 += str((int(i) + 5) % 10)
        for i in ticket[2]:
            if "0" <= i <= "9":
                str2 += str((int(i) + 5) % 10)
            elif 'A' <= i <= 'Z':
                if ord(i) + 10 > ord('Z'):
                    str2 += chr(ord(i) + 10 - 26)
                else:
                    str2 += chr(ord(i) + 10)
            else:
                if ord(i) + 15 > ord('z'):
                    str2 += chr(ord(i) + 15 - 26)
                else:
                    str2 += chr(ord(i) + 15)
        return str1, str2

    session = requests.Session()
    username, password = des(username, password)
    data = {
        "IDToken1": username,
        "IDToken2": password,
        "IDToken3": "",
        "goto": "aHR0cDovL2lkbS5zd3UuZWR1LmNuL2FtL29hdXRoMi9hdXRob3JpemU/c2VydmljZT1pbml0U2VydmljZSZyZXNwb25zZV90eXBlPWNvZGUmY2xpZW50X2lkPTdjMXpva29samw5YmJpaG82eXVvJnNjb3BlPXVpZCtjbit1c2VySWRDb2RlJnJlZGlyZWN0X3VyaT1odHRwcyUzQSUyRiUyRnVhYWFwLnN3dS5lZHUuY24lMkZjYXMlMkZsb2dpbiUzRnNlcnZpY2UlM0RodHRwcyUyNTNBJTI1MkYlMjUyRnVhYWFwLnN3dS5lZHUuY24lMjUyRmNhcyUyNTJGb2F1dGgyLjAlMjUyRmNhbGxiYWNrQXV0aG9yaXplJTI2b3JpZ2luYWxSZXF1ZXN0VXJsJTNEaHR0cHMlMjUzQSUyNTJGJTI1MkZ1YWFhcC5zd3UuZWR1LmNuJTI1MkZjYXMlMjUyRm9hdXRoMi4wJTI1MkZhdXRob3JpemUlMjUzRnJlc3BvbnNlX3R5cGUlMjUzRGNvZGUlMjUyNmNsaWVudF9pZCUyNTNEY2FzNiUyNTI2cmVkaXJlY3RfdXJpJTI1M0RodHRwcyUyNTI1M0ElMjUyNTJGJTI1MjUyRm9mLnN3dS5lZHUuY24lMjUyNTNBNDQzJTI1MjUyRmNhcyUyNTI1MkZvYXV0aCUyNTI1MkZjYWxsYmFjayUyNTI1MkZTV1VfQ0FTMl9GRURFUkFMJTI1MjZzdGF0ZSUyNTNEZTFlMTczODhlNzU4MjY3YjFiNzI2ZjM4Mjg0NDM5MWElMjUyNnNjb3BlJTI1M0RzaW1wbGUlMjZmZWRlcmFsRW5hYmxlJTNEdHJ1ZSZkZWNpc2lvbj1BbGxvdw==",
        "gotoOnFail": "",
        "sunQueryParamsString": "cmVhbG09LyZzZXJ2aWNlPWluaXRTZXJ2aWNlJg==",
        "encoded": "true",
        "gx_charset": "UTF-8"
    }
    response = session.get(
        "https://of.swu.edu.cn/cas/oauth/login/SWU_CAS2_FEDERAL?service=https%3A%2F%2Fof.swu.edu.cn%2Fgateway%2Ffighter-middle%2Fapi%2Fintegrate%2Fuaap%2Fcas%2Fresolve-cas-return%3Fnext%3Dhttps%253A%252F%252Fof.swu.edu.cn%252F%2523%252FcasLogin%253Ffrom%253D%25252FappCenter",
        timeout=timeout)
    state = urllib.parse.unquote(urllib.parse.unquote(response.url)).split("state=")[1][0:32]
    try:
        # 处理登录后的重定向，获取票据
        response = session.post("https://idm.swu.edu.cn/am/UI/Login", data=data, allow_redirects=True, timeout=timeout)

        # 安全获取ticket参数
        if "ticket=" not in response.url:
            raise Exception("登录失败：无法获取票据参数")
        ticket = response.url.split("ticket=")[1]

        str1, str2 = transform(ticket)
        CD = f"CD-{str1}-{str2}-wiie://777.643.675.751:3537/rph"
        url = urllib.parse.unquote(
            f"https://of.swu.edu.cn/cas/oauth/callback/SWU_CAS2_FEDERAL?code={CD}@@hxbeat&state={state}")

        response = session.get(url, allow_redirects=True)

        # 安全获取ST参数
        if "ticket=" not in response.url:
            raise Exception("登录失败：无法获取ST参数")
        ST = response.url.split("ticket=")[1]

        # 安全获取token
        token_response = requests.get(
            f"https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/exchange-token?token={ST}&remember=true",
            timeout=timeout).json()
        if "data" not in token_response:
            raise Exception("登录失败：无法获取访问令牌")

        token = token_response["data"]
        return token
    except Exception as e:
        # 捕获所有可能的异常并提供明确的错误信息
        raise Exception(f"获取令牌失败：{str(e)}")

def get_student_id(token, timeout=10):
    url = "https://of.swu.edu.cn/gateway/fighter-middle/api/auth/user?appType=fighter-portal"
    headers = {"fighter-auth-token": token}
    student_id = requests.get(url, headers=headers, timeout=timeout).json()["data"]["subject"]["username"]
    return student_id

def get_dormitory(token, timeout = 10):
    url = "https://of.swu.edu.cn/gateway/fighter-baida/api/cqlc/getDormitory"
    headers = {"fighter-auth-token": token, "Content-Type": "application/json;charset=UTF-8"}
    response = requests.post(url, headers=headers, data=json.dumps({}), timeout=timeout)
    return response.json()

def get_transition_today(token, timeout=10):
    url = "https://of.swu.edu.cn//gateway/fighter-baida/api/cqtj/getTransitionByToday"
    headers = {"fighter-auth-token": token}
    data = {"pageNum": 1,"pageSize": 1,}
    response = requests.post(url, headers=headers, data=data,timeout=timeout).json()["data"]["records"]
    return response[0] if response else None