from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import urllib.parse
import requests
import os
import ddddocr
import json
import re
from des import des
from identity import submit_identity_selection_if_needed


def debug_print(message: object) -> None:
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(message)

def transform(ticket: str) -> str:
    result = ""
    for char in ticket:
        if char in '-:/':
            result += char
            continue
        if '0' <= char <= '9':
            result += str((int(char) + 5) % 10)
        elif 'A' <= char <= 'Z':
            new_ord = ord(char) + 10
            if new_ord > ord('Z'):
                new_ord -= 26
            result += chr(new_ord)
        elif 'a' <= char <= 'z':
            new_ord = ord(char) + 15
            if new_ord > ord('z'):
                new_ord -= 26
            result += chr(new_ord)
        else:
            result += char
    return result

def get_token(username: str, password: str, timeout: int = 10) -> str:
    session = requests.Session()
    url = "https://of.swu.edu.cn/cas/oauth/login/SWU_CAS2_FEDERAL?service=https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/resolve-cas-return?next=https://of.swu.edu.cn/#/casLogin?from=/appCenter"
    response = session.get(url=url, timeout=timeout)
    state = re.search(r'state%3D([a-f0-9]{32})', response.url)
    state = state.group(1) if state else None
    debug_print(f"state:{state}")
    url = f"https://idm.swu.edu.cn/am/UI/Login?realm=/&service=initService&goto=http://idm.swu.edu.cn/am/oauth2/authorize?service=initService&response_type=code&client_id=7c1zokoljl9bbiho6yuo&scope=uid cn userIdCode&redirect_uri=https://uaaap.swu.edu.cn/cas/login?service=https://uaaap.swu.edu.cn/cas/oauth2.0/callbackAuthorize&originalRequestUrl=https://uaaap.swu.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=cas6&redirect_uri=https%3A%2F%2Fof.swu.edu.cn%3A443%2Fcas%2Foauth%2Fcallback%2FSWU_CAS2_FEDERAL&state={state}&scope=simple&federalEnable=true&decision=Allow"
    response = session.get(url=url, timeout=timeout)
    soup = BeautifulSoup(response.text, 'html.parser')
    code_random = soup.find('input', {'id': 'codeRandom'})
    random = code_random.get('value') if code_random else None
    debug_print(f"random:{random}")
    username, password = des(username, password, random)
    url = "https://idm.swu.edu.cn/am/validate.code"
    response = session.get(url)
    img = Image.open(BytesIO(response.content))
    ocr = ddddocr.DdddOcr(
        show_ad=False,
        use_gpu=False
    )
    code = ocr.classification(img)
    debug_print(f"code:{code}")
    data = {
        "IDToken1": username,
        "IDToken2": password,
        "IDToken3": "",
        "goto": "aHR0cDovL2lkbS5zd3UuZWR1LmNuL2FtL29hdXRoMi9hdXRob3JpemU/c2VydmljZT1pbml0U2VydmljZSZyZXNwb25zZV90eXBlPWNvZGUmY2xpZW50X2lkPTdjMXpva29samw5YmJpaG82eXVvJnNjb3BlPXVpZCtjbit1c2VySWRDb2RlJnJlZGlyZWN0X3VyaT1odHRwcyUzQSUyRiUyRnVhYWFwLnN3dS5lZHUuY24lMkZjYXMlMkZsb2dpbiUzRnNlcnZpY2UlM0RodHRwcyUyNTNBJTI1MkYlMjUyRnVhYWFwLnN3dS5lZHUuY24lMjUyRmNhcyUyNTJGb2F1dGgyLjAlMjUyRmNhbGxiYWNrQXV0aG9yaXplJTI2b3JpZ2luYWxSZXF1ZXN0VXJsJTNEaHR0cHMlMjUzQSUyNTJGJTI1MkZ1YWFhcC5zd3UuZWR1LmNuJTI1MkZjYXMlMjUyRm9hdXRoMi4wJTI1MkZhdXRob3JpemUlMjUzRnJlc3BvbnNlX3R5cGUlMjUzRGNvZGUlMjUyNmNsaWVudF9pZCUyNTNEY2FzNiUyNTI2cmVkaXJlY3RfdXJpJTI1M0RodHRwcyUyNTI1M0ElMjUyNTJGJTI1MjUyRm9mLnN3dS5lZHUuY24lMjUyNTNBNDQzJTI1MjUyRmNhcyUyNTI1MkZvYXV0aCUyNTI1MkZjYWxsYmFjayUyNTI1MkZTV1VfQ0FTMl9GRURFUkFMJTI1MjZzdGF0ZSUyNTNEZTFlMTczODhlNzU4MjY3YjFiNzI2ZjM4Mjg0NDM5MWElMjUyNnNjb3BlJTI1M0RzaW1wbGUlMjZmZWRlcmFsRW5hYmxlJTNEdHJ1ZSZkZWNpc2lvbj1BbGxvdw==",
        "gotoOnFail": "",
        "validateCode": code,
        "sunQueryParamsString": "cmVhbG09LyZzZXJ2aWNlPWluaXRTZXJ2aWNlJg==",
        "encoded": "true",
        "gx_charset": "UTF-8"
    }
    url = "https://idm.swu.edu.cn/am/UI/Login"
    response = session.post(url=url,data=data, timeout=10)
    response = submit_identity_selection_if_needed(
        session,
        response,
        login_url=url,
        goto_value=data["goto"],
        timeout=timeout,
    )
    debug_print(response.url)
    if "ticket" not in response.url:
        return ""
    ticket_st = urllib.parse.unquote(response.url).split("ticket=")[1]
    ticket_cd = transform(ticket_st)
    url = f"https://of.swu.edu.cn/cas/oauth/callback/SWU_CAS2_FEDERAL?code={ticket_cd}@@hxbeat&state={state}"
    response = session.get(url=url,timeout=timeout)
    if "ticket=" not in response.url:
        return ""
    token_st = response.url.split("ticket=")[1]
    url = f"https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/exchange-token?token={token_st}&remember=true"
    token_response = session.get(url=url,timeout=timeout).json()
    if "data" not in token_response:
        return ""
    token = token_response["data"]
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(f"token:{token}")
    return token

def get_student_id(token: str, timeout: int = 10) -> str:
    headers = {"fighter-auth-token": token}
    student_id = requests.get(url="https://of.swu.edu.cn/gateway/fighter-middle/api/auth/user?appType=fighter-portal", headers=headers, timeout=timeout).json()["data"]["subject"]["username"]
    return student_id

def get_dormitory(token: str, timeout: int = 10) -> dict[str, str]:
    headers = {"fighter-auth-token": token, "Content-Type": "application/json;charset=UTF-8"}
    response = requests.post(url="https://of.swu.edu.cn/gateway/fighter-baida/api/cqlc/getDormitory", headers=headers, data=json.dumps({}), timeout=timeout)
    return response.json()

def get_transition_today(token: str, timeout: int = 10) -> dict[str, str] | None:
    headers = {"fighter-auth-token": token}
    data = {"pageNum": 1,"pageSize": 1,}
    response = requests.post(url="https://of.swu.edu.cn//gateway/fighter-baida/api/cqtj/getTransitionByToday", headers=headers, data=data,timeout=timeout).json()["data"]["records"]
    return response[0] if response else None

