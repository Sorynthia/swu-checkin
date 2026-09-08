import time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
import os
import qrcode

NEXT_URL = "https://of.swu.edu.cn/#/casLogin?from=%2FappCenter"
SERVICE_URL = (
	"https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/resolve-cas-return?"
	f"next={quote(NEXT_URL, safe='')}"
)
LOGIN_URL = f"https://of.swu.edu.cn/cas/oauth/login/DINGTALK?service={quote(SERVICE_URL, safe='')}"
QR_PAGE_URL = "https://login.dingtalk.com/login/qrcode.htm"
QR_GENERATE_URL = "https://login.dingtalk.com/user/qrcode/generate"
QR_POLL_URL = "https://login.dingtalk.com/login/login_with_qr"
CALLBACK_URL = "https://of.swu.edu.cn/cas/oauth/callback/DINGTALK"
EXCHANGE_TOKEN_URL = "https://of.swu.edu.cn/gateway/fighter-middle/api/integrate/uaap/cas/exchange-token"
DEFAULT_HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
	"Referer": "https://login.dingtalk.com/",
}


def debug_print(message: object) -> None:
	if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
		print(message)


class LoggedSession(requests.Session):
	def request(self, method, url, *args, **kwargs):
		response = super().request(method, url, *args, **kwargs)
		location = response.headers.get("Location")
		redirect_suffix = f" -> {location}" if location else ""
		debug_print(f"[{method.upper()}] {response.url} ({response.status_code}){redirect_suffix}")
		return response


def create_session() -> requests.Session:
	session = LoggedSession()
	session.headers.update(DEFAULT_HEADERS)
	return session


def extract_state(redirect_url: str) -> str:
	decoded_url = unquote(unquote(redirect_url))
	parsed = urlparse(decoded_url)
	state = parse_qs(parsed.query).get("state", [None])[0]
	if not state:
		raise ValueError("未能从跳转链接中提取 state")
	return state


def extract_app_id(goto: str) -> str:
	app_id = parse_qs(urlparse(goto).query).get("appid", [None])[0]
	if not app_id:
		raise ValueError("未能从 goto 提取 appid")
	return app_id


def save_qr_image(qr_content: str, output_path: Path) -> Path:
	image = qrcode.make(qr_content)
	image.save(output_path)
	return output_path


def request_qr_page(session: requests.Session) -> tuple[str, str, str]:
	response = session.get(LOGIN_URL, timeout=10, allow_redirects=True)
	response.raise_for_status()
	state = extract_state(response.url)
	goto = (
		"https://oapi.dingtalk.com/connect/oauth2/sns_authorize?"
		"response_type=code&appid=dinggam4ayb6ahjixiez&scope=snsapi_login&"
		f"redirect_uri={CALLBACK_URL}&state={state}"
	)
	qr_page_response = session.get(QR_PAGE_URL, params={"goto": goto}, timeout=10)
	qr_page_response.raise_for_status()
	return state, goto, extract_app_id(goto)


def generate_qr_code(session: requests.Session, app_id: str) -> str:
	response = session.get(
		QR_GENERATE_URL,
		params={"bizScene": "http_third_party", "sceneId": app_id},
		timeout=10,
		headers=DEFAULT_HEADERS,
	)
	response.raise_for_status()
	payload = response.json()
	if not payload.get("success") or not payload.get("result"):
		raise ValueError("二维码生成失败")
	return payload["result"]


def build_qr_content(code: str, app_id: str, goto: str) -> str:
	redirect_uri = parse_qs(urlparse(goto).query).get("redirect_uri", [None])[0]
	if not redirect_uri:
		raise ValueError("未能从 goto 提取 redirect_uri")
	return (
		"https://oapi.dingtalk.com/connect/qrcommit?showmenu=false"
		f"&code={code}&appid={app_id}&redirect_uri={quote(redirect_uri, safe='')}"
	)


def poll_qr_status(session: requests.Session, goto: str, code: str, app_id: str, timeout: int = 120) -> str:
	deadline = time.time() + timeout

	while time.time() < deadline:
		data = {
			"qrCode": code,
			"goto": goto,
			"pdmToken": "",
			"bizScene": "http_third_party",
			"sceneId": app_id,
		}

		response = session.post(QR_POLL_URL, data=data, timeout=10, headers={"Referer": QR_PAGE_URL, **DEFAULT_HEADERS})
		response.raise_for_status()
		payload = response.json()
		if payload.get("success"):
			redirect_url = payload.get("data")
			if not redirect_url:
				raise ValueError("二维码轮询成功但缺少跳转链接")
			login_tmp_code = parse_qs(urlparse(redirect_url).query).get("loginTmpCode", [None])[0]
			if not login_tmp_code:
				raise ValueError("二维码轮询成功但缺少 loginTmpCode")
			return redirect_url

		status = str(payload.get("code", ""))
		if status == "11041":
			print("二维码已扫描，等待确认")
		elif status == "11021":
			pass
		elif status == "11019":
			raise TimeoutError("二维码已过期，请重新生成")
		else:
			message = payload.get("msg") or payload.get("message") or payload
			print(f"轮询状态: {status} {message}")
		time.sleep(2)

	raise TimeoutError("等待扫码超时")


def follow_callback_chain(session: requests.Session, redirect_url: str) -> tuple[str, str]:
	authorize_response = session.get(redirect_url, timeout=10, allow_redirects=False)
	authorize_response.raise_for_status()
	callback_url = authorize_response.headers.get("Location")
	if not callback_url:
		raise ValueError("钉钉授权未返回跳转链接")
	debug_print(f"钉钉授权回调: {callback_url}")
	current_url = callback_url
	for _ in range(10):
		response = session.get(current_url, timeout=10, allow_redirects=False)
		location = response.headers.get("Location")
		if not location:
			debug_print(f"回调链结束: {response.url} ({response.status_code})")
			return callback_url, response.url
		debug_print(f"继续跟随回调: {location}")
		current_url = location
	raise ValueError("回调重定向次数过多")


def extract_ticket(url: str) -> str:
	parsed = urlparse(url)
	ticket = parse_qs(parsed.query).get("ticket", [None])[0]
	if not ticket and parsed.fragment:
		fragment_query = parsed.fragment.split("?", 1)[1] if "?" in parsed.fragment else parsed.fragment
		ticket = parse_qs(fragment_query).get("ticket", [None])[0]
	if not ticket:
		raise ValueError("未能从链接中提取 ticket")
	return ticket


def exchange_token(session: requests.Session, ticket: str) -> str:
	response = session.get(
		EXCHANGE_TOKEN_URL,
		params={"token": ticket, "remember": "true"},
		timeout=10,
	)
	response.raise_for_status()
	payload = response.json()
	token = payload.get("data")
	if not token:
		raise ValueError("token 交换失败")
	return token


def dingding_qr_login(timeout: int = 120, qr_path: str = "dingding_qr.png") -> str:
	session = create_session()
	state, goto, app_id = request_qr_page(session)
	code = generate_qr_code(session, app_id)
	qr_content = build_qr_content(code, app_id, goto)
	debug_print(f"state: {state}")
	debug_print(f"appId: {app_id}")
	debug_print(f"qrCode: {code}")
	saved_path = save_qr_image(qr_content, Path(qr_path))
	print(f"二维码已保存到: {saved_path.resolve()}")
	redirect_url = poll_qr_status(session, goto, code, app_id, timeout=timeout)
	debug_print(f"扫码确认后跳转: {redirect_url}")
	callback_url, final_url = follow_callback_chain(session, redirect_url)
	ticket = extract_ticket(final_url)
	token = exchange_token(session, ticket)
	if os.getenv("SWUDK_DEBUG_CREDENTIALS") == "1":
		print(f"callback_url: {callback_url}")
		print(f"final_url: {final_url}")
		print(f"ticket: {ticket}")
		print(f"token: {token}")
	return token


if __name__ == "__main__":
	dingding_qr_login()
