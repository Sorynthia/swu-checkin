"""Helpers for SWU's optional student identity selection page."""

import re
from typing import Any

from bs4 import BeautifulSoup


_IDENTITY_CODES_RE = re.compile(r"(?:var|let|const)\s+defaultCodes\s*=\s*['\"]([^'\"]*)['\"]")


def choose_identity_code(html: str) -> str | None:
    """Choose postgraduate identity when SWU offers multiple identities."""

    if not re.search(r"(?:name|id)\s*=\s*['\"]identityDefault['\"]", html):
        return None
    match = _IDENTITY_CODES_RE.search(html)
    if not match:
        return None

    identities: list[tuple[str, str]] = []
    for item in match.group(1).split(";"):
        code, separator, label = item.partition(":")
        code = code.strip()
        if separator and code:
            identities.append((code, label.strip()))
    if not identities:
        return None

    for code, label in identities:
        normalized = f"{code} {label}".lower()
        if any(marker in normalized for marker in ("yanjiusheng", "研究生", "硕士", "博士")):
            return code
    return identities[0][0]


def identity_selection_data(html: str, identity_code: str, *, goto_value: str) -> dict[str, str]:
    """Build the IDM form payload for a selected identity."""

    data = {
        "IDToken1": identity_code,
        "IDToken2": "",
        "IDToken3": "",
        "goto": goto_value,
        "gotoOnFail": "",
        "SunQueryParamsString": "",
        "encoded": "true",
        "gx_charset": "UTF-8",
    }
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", attrs={"name": "Login"})
    if not form:
        return data
    for field in form.find_all("input"):
        name = field.get("name")
        if name and name not in {"IDToken1", "IDToken2", "IDToken3"}:
            data[name] = str(field.get("value") or "")
    return data


def submit_identity_selection_if_needed(
    session: Any,
    response: Any,
    *,
    login_url: str,
    goto_value: str,
    **request_kwargs: Any,
) -> Any:
    """Submit the preferred identity when the initial login response asks for it."""

    if "ticket" in str(response.url):
        return response
    identity_code = choose_identity_code(response.text)
    if not identity_code:
        return response
    data = identity_selection_data(response.text, identity_code, goto_value=goto_value)
    return session.post(login_url, data=data, **request_kwargs)
