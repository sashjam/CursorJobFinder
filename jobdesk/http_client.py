from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

import certifi

from jobdesk.config import hh_user_agent

USER_AGENT = "JobDesk/1.0 (personal job search; +https://github.com/local/jobdesk)"

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def fetch_bytes(
    url: str,
    *,
    timeout: float = 25.0,
    headers: dict[str, str] | None = None,
) -> bytes:
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return resp.read()


def fetch_text(
    url: str,
    *,
    timeout: float = 25.0,
    encoding: str = "utf-8",
    headers: dict[str, str] | None = None,
) -> str:
    data = fetch_bytes(url, timeout=timeout, headers=headers)
    return data.decode(encoding, errors="replace")


def fetch_json(
    url: str,
    *,
    timeout: float = 25.0,
    headers: dict[str, str] | None = None,
) -> Any:
    raw = fetch_bytes(url, timeout=timeout, headers=headers)
    return json.loads(raw.decode("utf-8"))


def hh_headers() -> dict[str, str]:
    return {"User-Agent": hh_user_agent(), "Accept": "application/json"}
