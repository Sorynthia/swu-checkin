from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import urllib.parse
import requests
import os
import ddddocr
import json
import re

from .des import des
from .identity import submit_identity_selection_if_needed


# ===== 常量定义 =====
CAS_LOGIN_URL = "https://of.swu.edu.cn/cas/oauth/login/SWU_CAS2_FEDERAL"
CAS_SERVICE = "https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/resolve-cas-return?next=https://of.swu.edu.cn/#/casLogin?from=/appCenter"
IDM_BASE_URL = "https://idm.swu.edu.cn/am"
IDM_VALIDATE_CODE_URL = "https://idm.swu.edu.cn/am/validate.code"
CAS_CALLBACK_URL = "https://of.swu.edu.cn/cas/oauth/callback/SWU_CAS2_FEDERAL"
TOKEN_EXCHANGE_URL = "https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/exchange-token"
USER_INFO_URL = "https://of.swu.edu.cn/gateway/fighter-middle/api/auth/user"
DORMITORY_URL = "https://of.swu.edu.cn/gateway/fighter-baida/api/cqlc/getDormitory"
TRANSITION_TODAY_URL = "https://of.swu.edu.cn//gateway/fighter-baida/api/cqtj/getTransitionByToday"

# OAuth2 固定参数
OAUTH_GOTO_BASE64 = "aHR0cDovL2lkbS5zd3UuZWR1LmNuL2FtL29hdXRoMi9hdXRob3JpemU/c2VydmljZT1pbml0U2VydmljZSZyZXNwb25zZV90eXBlPWNvZGUmY2xpZW50X2lkPTdjMXpva29samw5YmJpaG82eXVvJnNjb3BlPXVpZCtjbit1c2VySWRDb2RlJnJlZGlyZWN0X3VyaT1odHRwcyUzQSUyRiUyRnVhYWFwLnN3dS5lZHUuY24lMkZjYXMlMkZsb2dpbiUzRnNlcnZpY2UlM0RodHRwcyUyNTNBJTI1MkYlMjUyRnVhYWFwLnN3dS5lZHUuY24lMjUyRmNhcyUyNTJGb2F1dGgyLjAlMjUyRmNhbGxiYWNrQXV0aG9yaXplJTI2b3JpZ2luYWxSZXF1ZXN0VXJsJTNEaHR0cHMlMjUzQSUyNTJGJTI1MkZ1YWFhcC5zd3UuZWR1LmNuJTI1MkZjYXMlMjUyRm9hdXRoMi4wJTI1MkZhdXRob3JpemUlMjUzRnJlc3BvbnNlX3R5cGUlMjUzRGNvZGUlMjUyNmNsaWVudF9pZCUyNTNEY2FzNiUyNTI2cmVkaXJlY3RfdXJpJTI1M0RodHRwcyUyNTI1M0ElMjUyNTJGJTI1MjUyRm9mLnN3dS5lZHUuY24lMjUyNTNBNDQzJTI1MjUyRmNhcyUyNTI1MkZvYXV0aCUyNTI1MkZjYWxsYmFjayUyNTI1MkZTV1VfQ0FTMl9GRURFUkFMJTI1MjZzdGF0ZSUyNTNEZTFlMTczODhlNzU4MjY3YjFiNzI2ZjM4Mjg0NDM5MWElMjUyNnNjb3BlJTI1M0RzaW1wbGUlMjZmZWRlcmFsRW5hYmxlJTNEdHJ1ZSZkZWNpc2lvbj1BbGxvdw=="


# ===== 辅助函数 =====
def debug_print(message: object) -> None:
    """调试模式输出"""
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(message)


def transform_ticket(ticket: str) -> str:
    """
    转换 ticket 编码
    数字: +5 模 10
    大写字母: +10 (超Z循环)
    小写字母: +15 (超z循环)
    """
    result = ""
    for char in ticket:
        if char in '-:/':
            result += char
        elif '0' <= char <= '9':
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


def build_idm_login_url(state: str) -> str:
    """构建 IDM 登录 URL"""
    return (
        f"{IDM_BASE_URL}/UI/Login"
        f"?realm=/&service=initService"
        f"&goto=http://idm.swu.edu.cn/am/oauth2/authorize"
        f"?service=initService&response_type=code"
        f"&client_id=7c1zokoljl9bbiho6yuo"
        f"&scope=uid cn userIdCode"
        f"&redirect_uri=https://uaaap.swu.edu.cn/cas/login"
        f"?service=https://uaaap.swu.edu.cn/cas/oauth2.0/callbackAuthorize"
        f"&originalRequestUrl=https://uaaap.swu.edu.cn/cas/oauth2.0/authorize"
        f"?response_type=code&client_id=cas6"
        f"&redirect_uri=https%3A%2F%2Fof.swu.edu.cn%3A443%2Fcas%2Foauth%2Fcallback%2FSWU_CAS2_FEDERAL"
        f"&state={state}&scope=simple&federalEnable=true&decision=Allow"
    )


def extract_state_from_url(url: str) -> str:
    """从跳转 URL 提取 state 参数"""
    match = re.search(r'state%3D([a-f0-9]{32})', url)
    return match.group(1) if match else None


def parse_code_random(html: str) -> str:
    """从登录页 HTML 解析 codeRandom"""
    soup = BeautifulSoup(html, 'html.parser')
    code_random = soup.find('input', {'id': 'codeRandom'})
    return code_random.get('value') if code_random else None


def recognize_captcha(session: requests.Session) -> str:
    """OCR 识别验证码"""
    response = session.get(IDM_VALIDATE_CODE_URL)
    img = Image.open(BytesIO(response.content))
    ocr = ddddocr.DdddOcr(show_ad=False, use_gpu=False)
    return ocr.classification(img)


def build_login_form_data(username: str, password: str, captcha: str) -> dict:
    """构建登录表单数据"""
    return {
        "IDToken1": username,
        "IDToken2": password,
        "IDToken3": "",
        "goto": OAUTH_GOTO_BASE64,
        "gotoOnFail": "",
        "validateCode": captcha,
        "sunQueryParamsString": "cmVhbG09LyZzZXJ2aWNlPWluaXRTZXJ2aWNlJg==",
        "encoded": "true",
        "gx_charset": "UTF-8"
    }


def extract_ticket_from_url(url: str) -> str:
    """从回调 URL 提取 ticket"""
    if "ticket=" not in url:
        return None
    return urllib.parse.unquote(url).split("ticket=")[1]


# ===== 主要登录流程 =====
def get_token(username: str, password: str, timeout: int = 10) -> str:
    """
    执行完整登录流程，获取 fighter-auth-token
    
    流程:
        1. 访问 CAS 登录页，获取 OAuth state
        2. 跳转 IDM 登录页，解析 codeRandom
        3. DES 加密用户名和密码
        4. OCR 识别验证码
        5. 提交登录表单
        6. 处理身份选择（研究生/本科生）
        7. 从回调 URL 提取 ticket，转换编码
        8. 用 ticket 换取 token
    
    返回:
        成功返回 token，失败返回空字符串
    """
    session = requests.Session()
    
    # 步骤 1: 获取 OAuth state
    response = session.get(
        CAS_LOGIN_URL,
        params={"service": CAS_SERVICE},
        timeout=timeout
    )
    state = extract_state_from_url(response.url)
    debug_print(f"state: {state}")
    
    if not state:
        return ""
    
    # 步骤 2: 访问 IDM 登录页
    idm_login_url = build_idm_login_url(state)
    response = session.get(idm_login_url, timeout=timeout)
    code_random = parse_code_random(response.text)
    debug_print(f"random: {code_random}")
    
    if not code_random:
        return ""
    
    # 步骤 3: DES 加密凭证
    encrypted_username, encrypted_password = des(username, password, code_random)
    
    # 步骤 4: OCR 识别验证码
    captcha = recognize_captcha(session)
    debug_print(f"code: {captcha}")
    
    # 步骤 5: 提交登录表单
    form_data = build_login_form_data(
        encrypted_username,
        encrypted_password,
        captcha
    )
    response = session.post(
        f"{IDM_BASE_URL}/UI/Login",
        data=form_data,
        timeout=timeout
    )
    
    # 步骤 6: 处理身份选择
    response = submit_identity_selection_if_needed(
        session,
        response,
        login_url=f"{IDM_BASE_URL}/UI/Login",
        goto_value=OAUTH_GOTO_BASE64,
        timeout=timeout,
    )
    
    debug_print(response.url)
    
    # 步骤 7: 提取并转换 ticket
    ticket_st = extract_ticket_from_url(response.url)
    if not ticket_st:
        return ""
    
    ticket_cd = transform_ticket(ticket_st)
    
    # 步骤 8a: 使用转换后的 ticket 访问回调
    callback_url = f"{CAS_CALLBACK_URL}?code={ticket_cd}@@hxbeat&state={state}"
    response = session.get(callback_url, timeout=timeout)
    
    # 步骤 8b: 从最终回调 URL 获取 token ticket
    token_st = extract_ticket_from_url(response.url)
    if not token_st:
        return ""
    
    # 步骤 8c: 用 token ticket 换取最终 token
    exchange_url = f"{TOKEN_EXCHANGE_URL}?token={token_st}&remember=true"
    token_response = session.get(exchange_url, timeout=timeout).json()
    
    if "data" not in token_response:
        return ""
    
    token = token_response["data"]
    debug_print(f"token: {token}")
    
    return token


def get_student_id(token: str, timeout: int = 10) -> str:
    """获取学号"""
    headers = {"fighter-auth-token": token}
    response = requests.get(
        USER_INFO_URL,
        params={"appType": "fighter-portal"},
        headers=headers,
        timeout=timeout
    )
    return response.json()["data"]["subject"]["username"]


def get_dormitory(token: str, timeout: int = 10) -> dict:
    """获取宿舍信息"""
    headers = {
        "fighter-auth-token": token,
        "Content-Type": "application/json;charset=UTF-8"
    }
    response = requests.post(
        DORMITORY_URL,
        headers=headers,
        data=json.dumps({}),
        timeout=timeout
    )
    return response.json()


def get_transition_today(token: str, timeout: int = 10) -> dict | None:
    """获取今日签到任务"""
    headers = {"fighter-auth-token": token}
    data = {"pageNum": 1, "pageSize": 1}
    response = requests.post(
        TRANSITION_TODAY_URL,
        headers=headers,
        data=data,
        timeout=timeout
    ).json()
    
    records = response.get("data", {}).get("records", [])
    return records[0] if records else None