import json
import re
import urllib
from getpass import getpass
import os
from pathlib import Path
from des import des
from io import BytesIO
import ddddocr
from bs4 import BeautifulSoup
from PIL import Image
import requests

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from identity import submit_identity_selection_if_needed


def debug_print(message: object) -> None:
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(message)


COOKIE_FILE = Path(__file__).with_name("swu_cookies.json")
COOKIE_FORMAT_VERSION = 1
COOKIE_MAX_BYTES = 64 * 1024
COOKIE_MAX_COUNT = 100
COOKIE_FIELDS = {"name", "value", "domain", "path", "secure", "expires"}
LOGIN_ENTRY_URL = "https://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?http://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?service=https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth"
LOGIN_SUCCESS_URL = "https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth"
TRANSFORM_TABLE = str.maketrans({
    **{str(digit): str((digit + 5) % 10) for digit in range(10)},
    **{
        chr(code): chr((code - ord('A') + 10) % 26 + ord('A'))
        for code in range(ord('A'), ord('Z') + 1)
    },
    **{
        chr(code): chr((code - ord('a') + 15) % 26 + ord('a'))
        for code in range(ord('a'), ord('z') + 1)
    },
})


def create_session() -> requests.Session:
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    session.headers.update(headers)
    return session


def _validate_cookie_payload(payload: object) -> list[dict[str, object]]:
    if type(payload) is not dict or set(payload) != {"version", "cookies"}:
        raise ValueError("invalid cookie payload")
    if type(payload["version"]) is not int or payload["version"] != COOKIE_FORMAT_VERSION:
        raise ValueError("unsupported cookie format")

    items = payload["cookies"]
    if type(items) is not list:
        raise ValueError("invalid cookie list")
    if len(items) > COOKIE_MAX_COUNT:
        raise ValueError("too many cookies")

    validated: list[dict[str, object]] = []
    for item in items:
        if type(item) is not dict or set(item) != COOKIE_FIELDS:
            raise ValueError("invalid cookie entry")
        if any(type(item[field]) is not str for field in ("name", "value", "domain", "path")):
            raise ValueError("invalid cookie string field")
        if not item["name"] or not item["path"].startswith("/"):
            raise ValueError("invalid cookie scope")
        if type(item["secure"]) is not bool:
            raise ValueError("invalid cookie secure flag")
        expires = item["expires"]
        if expires is not None and (type(expires) is not int or expires < 0):
            raise ValueError("invalid cookie expiry")
        validated.append(item)

    return validated


def save_cookies(session: requests.Session) -> None:
    payload = {
        "version": COOKIE_FORMAT_VERSION,
        "cookies": [
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
            }
            for cookie in session.cookies
        ],
    }
    _validate_cookie_payload(payload)
    content = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if len(content) > COOKIE_MAX_BYTES:
        raise ValueError("cookie data is too large")
    COOKIE_FILE.write_bytes(content)


def load_cookies(session: requests.Session) -> bool:
    if not COOKIE_FILE.exists():
        return False

    try:
        with COOKIE_FILE.open("rb") as file:
            content = file.read(COOKIE_MAX_BYTES + 1)
        if len(content) > COOKIE_MAX_BYTES:
            return False
        items = _validate_cookie_payload(json.loads(content.decode("utf-8")))

        cookies = requests.cookies.RequestsCookieJar()
        for item in items:
            cookies.set_cookie(
                requests.cookies.create_cookie(
                    name=item["name"],
                    value=item["value"],
                    domain=item["domain"],
                    path=item["path"],
                    secure=item["secure"],
                    expires=item["expires"],
                )
            )
        session.cookies.update(cookies)
    except (OSError, RecursionError, TypeError, UnicodeError, ValueError):
        return False

    return True


def is_authenticated_response(response: requests.Response) -> bool:
    url = response.url.lower()
    return (
        response.ok
        and 'cas/login' not in url
        and 'am/ui/login' not in url
        and 'validate.code' not in url
    )


def has_valid_cookies(session: requests.Session) -> bool:
    response = session.get(LOGIN_SUCCESS_URL, allow_redirects=True)
    return is_authenticated_response(response)


def transform(ticket: str) -> str:
    return ticket.translate(TRANSFORM_TABLE)



def login_with_credentials(session: requests.Session, username: str, password: str) -> requests.Session:
    response = session.get(url=LOGIN_ENTRY_URL)
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
    if "ticket=" not in response.url:
        raise RuntimeError("登录失败，未获取到 ticket，可能是账号、密码或验证码错误")

    ticket_st = urllib.parse.unquote(response.url).split("ticket=")[1]
    ticket_cd = transform(ticket_st)
    if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
        print(f"ticket_st:{ticket_st}")
        print(f"ticket_cd:{ticket_cd}")
    url = f"https://ywtb.swu.edu.cn/center-auth-server/outsideLink/auth/ZHI_LONG_AUTH2?back=http://ywtb.swu.edu.cn/center-auth-server/officeHallApplicationCode/cas/login?service=https://ywtb.swu.edu.cn/business-center-front/casPlusClient/auth&code={ticket_cd}@@hxbeat&state={state}"
    response = session.get(url=url)
    debug_print(response.url)

    if not is_authenticated_response(response):
        raise RuntimeError("登录流程已完成，但未进入已认证页面")

    save_cookies(session)
    return session


def get_authenticated_session(username: str, password: str) -> requests.Session:
    session = create_session()
    if load_cookies(session) and has_valid_cookies(session):
        print("已复用本地 cookie")
        return session

    if COOKIE_FILE.exists():
        COOKIE_FILE.unlink(missing_ok=True)
        session.cookies.clear()

    print("本地 cookie 不可用，执行重新登录")
    return login_with_credentials(session, username, password)



if __name__ == "__main__":
    username = os.getenv("SWUDK_USERNAME") or input("校园网账号：").strip()
    password = os.getenv("SWUDK_PASSWORD") or getpass("校园网密码：")
    session = get_authenticated_session(username, password)
