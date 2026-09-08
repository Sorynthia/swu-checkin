from io import BytesIO
from getpass import getpass
import os

from bs4 import BeautifulSoup
import ddddocr
import requests
from PIL import Image
from urllib.parse import unquote, parse_qs, urlparse
from des import des
from get_info import transform
from identity import submit_identity_selection_if_needed


def get_token(username: str, password: str) -> str:
    session = requests.Session()
    url = "https://of.swu.edu.cn/cas/oauth/login/SWU_CAS2_FEDERAL?service=https://of.swu.edu.cn/baida/#/microApp/workbench?appId=ab621bc9aa8e497603a9afcb0a41373b"
    response = session.get(url=url)
    url = unquote(unquote(response.url))
    parsed = urlparse(url)
    state = parse_qs(parsed.query).get("state", [None])[0]
    url = f"https://uaaap.swu.edu.cn/cas/login?service=https://uaaap.swu.edu.cn/cas/oauth2.0/callbackAuthorize&originalRequestUrl=https://uaaap.swu.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=cas6&redirect_uri=https://of.swu.edu.cn:443/cas/oauth/callback/SWU_CAS2_FEDERAL&state={state}&scope=simple&federalEnable=true#/microApp/workbench?appId=ab621bc9aa8e497603a9afcb0a41373b"
    response = session.get(url=url)
    soup = BeautifulSoup(response.text, 'html.parser')
    codeRandom = soup.find('input', {'id': 'codeRandom'}).get('value')
    username, password = des(username, password, codeRandom)
    url = "https://idm.swu.edu.cn/am/validate.code"
    response = session.get(url)
    img = Image.open(BytesIO(response.content))
    ocr = ddddocr.DdddOcr(
        show_ad=False,
        use_gpu=False
    )
    code = ocr.classification(img)
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
    parsed = urlparse(response.url)
    ticket_st = parse_qs(parsed.query).get("ticket", [None])[0]
    ticket_cd = transform(ticket_st)
    url = f"https://of.swu.edu.cn/cas/oauth/callback/SWU_CAS2_FEDERAL?code={ticket_cd}&state={state}"
    response = session.get(url=url)
    parsed = urlparse(response.url)
    ticket = parse_qs(parsed.query).get("ticket", [None])[0]
    url = "https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/to-cas-login?next=/&thirdPartyName=&frontUrl=https://of.swu.edu.cn/baida/#/casLogin"
    response = session.get(url=url)
    parsed = urlparse(response.url)
    ticket = parse_qs(parsed.query).get("ticket", [None])[0]
    url = f"https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/exchange-token?token={ticket}&remember=true"
    response = session.get(url=url)
    token = response.json().get("data")
    return token

if __name__ == "__main__":
    username = os.getenv("SWUDK_USERNAME") or input("校园网账号：").strip()
    password = os.getenv("SWUDK_PASSWORD") or getpass("校园网密码：")
    token = get_token(username, password)
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(token)
