import re
from io import BytesIO
import ddddocr
from bs4 import BeautifulSoup
from PIL import Image
from des import des
import requests
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity import submit_identity_selection_if_needed
timestamp = int(time.time() * 1000)
def verify(username: str, password: str, timeout: int = 10) -> bool:
    session = requests.Session()
    url = "https://of.swu.edu.cn/cas/oauth/login/SWU_CAS2_FEDERAL?service=https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/resolve-cas-return?next=https://of.swu.edu.cn/#/casLogin?from=/appCenter"
    response = session.get(url=url, timeout=timeout)
    state = re.search(r'state%3D([a-f0-9]{32})', response.url)
    state = state.group(1) if state else None
    # print(f"state:{state}")
    url = f"https://idm.swu.edu.cn/am/UI/Login?realm=/&service=initService&goto=http://idm.swu.edu.cn/am/oauth2/authorize?service=initService&response_type=code&client_id=7c1zokoljl9bbiho6yuo&scope=uid cn userIdCode&redirect_uri=https://uaaap.swu.edu.cn/cas/login?service=https://uaaap.swu.edu.cn/cas/oauth2.0/callbackAuthorize&originalRequestUrl=https://uaaap.swu.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=cas6&redirect_uri=https%3A%2F%2Fof.swu.edu.cn%3A443%2Fcas%2Foauth%2Fcallback%2FSWU_CAS2_FEDERAL&state={state}&scope=simple&federalEnable=true&decision=Allow"
    response = session.get(url=url, timeout=timeout)
    soup = BeautifulSoup(response.text, 'html.parser')
    code_random = soup.find('input', {'id': 'codeRandom'})
    random = code_random.get('value') if code_random else None
    # print(f"random:{random}")
    username, password = des(username, password, random)
    url = "https://idm.swu.edu.cn/am/validate.code"
    response = session.get(url)
    img = Image.open(BytesIO(response.content))
    ocr = ddddocr.DdddOcr(
        show_ad=False,
        use_gpu=False
    )
    code = ocr.classification(img)
    # print(f"code:{code}")
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
    response = session.post(url=url, data=data, timeout=10)
    response = submit_identity_selection_if_needed(
        session,
        response,
        login_url=url,
        goto_value=data["goto"],
        timeout=timeout,
    )
    if "ticket" not in response.url:
        return False
    else:
        return True


