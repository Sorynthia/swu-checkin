
import re
import urllib
from des import des
from io import BytesIO
import ddddocr
from bs4 import BeautifulSoup
from PIL import Image
import requests
import os
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



def get_token(username: str, password: str) -> str:
    session = requests.Session()
    headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Upgrade-Insecure-Requests': '1',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    session.headers.update(headers)
    url = "https://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?http://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?service=https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth"
    response = session.get(url=url)
    state = re.search(r'state%3D([a-f0-9]{32})', response.url)
    state = state.group(1) if state else None
    debug_print(f"state:{state}")
    url = f"https://uaaap.swu.edu.cn/cas/login?service=https://uaaap.swu.edu.cn/cas/oauth2.0/callbackAuthorize&originalRequestUrl=https://uaaap.swu.edu.cn/cas/oauth2.0/authorize?client_id=yzsmh&redirect_uri=https://ywtb.swu.edu.cn/center-auth-server/outsideLink/auth/ZHI_LONG_AUTH2?back=http://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?service=https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth&response_type=code&scope=simple&state={state}&federalEnable=true"
    response = session.get(url=url)
    soup = BeautifulSoup(response.text, 'html.parser')
    codeRandom = soup.find('input', {'id': 'codeRandom'}).get('value')
    debug_print(f"codeRandom:{codeRandom}")
    username, password = des(username, password, codeRandom)
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
        "goto": "aHR0cDovL2lkbS5zd3UuZWR1LmNuL2FtL29hdXRoMi9hdXRob3JpemU/c2VydmljZT1pbml0U2VydmljZSZyZXNwb25zZV90eXBlPWNvZGUmY2xpZW50X2lkPTdjMXpva29samw5YmJpaG82eXVvJnNjb3BlPXVpZCtjbit1c2VySWRDb2RlJnJlZGlyZWN0X3VyaT1odHRwcyUzQSUyRiUyRnVhYWFwLnN3dS5lZHUuY24lMkZjYXMlMkZsb2dpbiUzRnNlcnZpY2UlM0RodHRwcyUyNTNBJTI1MkYlMjUyRnVhYWFwLnN3dS5lZHUuY24lMjUyRmNhcyUyNTJGb2F1dGgyLjAlMjUyRmNhbGxiYWNrQXV0aG9yaXplJTI2b3JpZ2luYWxSZXF1ZXN0VXJsJTNEaHR0cHMlMjUzQSUyNTJGJTI1MkZ1YWFhcC5zd3UuZWR1LmNuJTI1MkZjYXMlMjUyRm9hdXRoMi4wJTI1MkZhdXRob3JpemUlMjUzRmNsaWVudF9pZCUyNTNEeXpzbWglMjUyNnJlZGlyZWN0X3VyaSUyNTNEaHR0cHMlMjUyNTNBJTI1MjUyRiUyNTI1MkZ5d3RiLnN3dS5lZHUuY24lMjUyNTJGY2VudGVyLWF1dGgtc2VydmVyJTI1MjUyRm91dHNpZGVMaW5rJTI1MjUyRmF1dGglMjUyNTJGWkhJX0xPTkdfQVVUSDIlMjUyNTNGYmFjayUyNTI1M0RodHRwJTI1MjUyNTNBJTI1MjUyNTJGJTI1MjUyNTJGeXd0Yi5zd3UuZWR1LmNuJTI1MjUyNTJGY2VudGVyLWF1dGgtc2VydmVyJTI1MjUyNTJGb2ZmaWNlSGFsbEFwcGxpY2F0aW9uQ29kZSUyNTI1MjUyRmNhcyUyNTI1MjUyRmxvZ2luJTI1MjUyNTNGc2VydmljZSUyNTI1MjUzRGh0dHBzJTI1MjUyNTI1M0ElMjUyNTI1MjUyRiUyNTI1MjUyNTJGeXd0Yi5zd3UuZWR1LmNuJTI1MjUyNTI1MkZidXNpbmVzcy1jZW50ZXItZnJvbnQlMjUyNTI1MjUyRmNhc1BsdXNDbGllbnQlMjUyNTI1MjUyRmF1dGglMjUyNnJlc3BvbnNlX3R5cGUlMjUzRGNvZGUlMjUyNnNjb3BlJTI1M0RzaW1wbGUlMjUyNnN0YXRlJTI1M0RhOWFlMmMyOWFkOWM0OTY4OTM0ZWUzZjE3YjliYWZiOCUyNmZlZGVyYWxFbmFibGUlM0R0cnVlJmRlY2lzaW9uPUFsbG93",
        "gotoOnFail": "",
        "validateCode": code,
        "sunQueryParamsString": "cmVhbG09LyZzZXJ2aWNlPWluaXRTZXJ2aWNlJg==",
        "encoded": "true",
        "gx_charset": "UTF-8"
    }
    url = "https://idm.swu.edu.cn/am/UI/Login"
    response = session.post(url=url, data=data)
    response = submit_identity_selection_if_needed(
        session,
        response,
        login_url=url,
        goto_value=data["goto"],
    )
    ticket_st = urllib.parse.unquote(response.url).split("ticket=")[1]
    ticket_cd = transform(ticket_st)
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(f"ticket_st:{ticket_st}")
        print(f"ticket_cd:{ticket_cd}")
    url = f"https://ywtb.swu.edu.cn/center-auth-server/outsideLink/auth/ZHI_LONG_AUTH2?back=http://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?service=https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth&code={ticket_cd}@@hxbeat&state={state}"
    response = session.get(url=url)
    debug_print(response.url)
    url = "https://ywtb.swu.edu.cn/business-center-front/cApplication/getApplicationUrl?applicationCode=DHsxE0c270&clientCategory=PC&appCode=new-office-hall-pc&appKey=pc-officeHall&universityId=106350"
    response = session.get(url=url)
    url = response.json().get("content", {}).get("redirectUrl")
    response = session.get(url=url, allow_redirects=False)
    url = response.headers.get("Location")
    debug_print(url)
    state = re.search(r'state=([a-f0-9]{32})', url)
    state = state.group(1) if state else None
    response = session.get(url=url)
    debug_print(response.url)
    ticket_st = urllib.parse.unquote(response.url).split("ticket=")[1]
    ticket_cd = transform(ticket_st)
    url = f"https://of.swu.edu.cn/cas/oauth/callback/SWU_CAS2_FEDERAL?code={ticket_cd}@@hxbeat&state={state}"
    response = session.get(url=url)
    debug_print(response.url)
    url = response.url+"&remember=true"
    response = session.get(url=url)
    debug_print(response.text)
