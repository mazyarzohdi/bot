"""Minimal synchronous 3x-ui (MHSanaei) panel API client, for the Django
web panel process.

The bot already has a full async client (services/xui_client.py, built on
aiohttp) — but that process is a separate aiogram polling loop, and the
panel's venv doesn't include aiohttp. This is a sync (stdlib urllib only)
equivalent covering everything the reseller panel needs to create and
fully manage its own clients directly from the web panel: add, update
(rename/resize/change expiry/enable/disable), delete, reset traffic, and
read back links/traffic. Uses the exact same request shapes as the bot's
client so both stay compatible with the same 3x-ui panel installs.
"""

import json
import random
import string
import time
import urllib.error
import urllib.request


class XUIError(Exception):
    pass


def _request(base_url: str, api_token: str, method: str, path: str, data=None, timeout: float = 15):
    url = base_url.rstrip("/") + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        raise XUIError(f"HTTP {e.code}: {text[:300]}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise XUIError(f"Connection failed: {e}") from e

    try:
        result = json.loads(text) if text else {}
    except ValueError:
        raise XUIError(f"Invalid response from panel: {text[:300]}")

    if isinstance(result, dict) and result.get("success") is False:
        raise XUIError(result.get("msg", "Panel API error"))
    return result


def get_client(base_url: str, api_token: str, email: str) -> dict | None:
    result = _request(base_url, api_token, "GET", f"/panel/api/clients/get/{email}")
    return result.get("obj")


def add_client(
    base_url: str, api_token: str, *, email: str, inbound_ids: list[int],
    total_gb: float, expiry_time_ms: int, sub_id: str = "", comment: str = "", tg_id: int = 0,
) -> dict:
    total_bytes = int(total_gb * (1024 ** 3)) if total_gb > 0 else 0
    client_data = {
        "email": email, "totalGB": total_bytes, "expiryTime": expiry_time_ms,
        "tgId": tg_id, "comment": comment, "enable": True,
    }
    if sub_id:
        client_data["subId"] = sub_id
    payload = {"inboundIds": inbound_ids, "client": client_data}
    result = _request(base_url, api_token, "POST", "/panel/api/clients/add", payload)
    return result.get("obj", result)


def update_client(base_url: str, api_token: str, email: str, client_data: dict) -> dict:
    result = _request(base_url, api_token, "POST", f"/panel/api/clients/update/{email}", client_data)
    return result.get("obj", result)


def delete_client(base_url: str, api_token: str, email: str, keep_traffic: bool = False, timeout: float = 15) -> bool:
    """Delete a client from a 3x-ui panel. Returns True on confirmed
    success, False otherwise (network error, auth error, or the panel
    reporting failure) — the caller decides whether that's fatal."""
    if not base_url or not api_token or not email:
        return False
    path = f"/panel/api/clients/del/{email}"
    if keep_traffic:
        path += "?keepTraffic=1"
    try:
        _request(base_url, api_token, "POST", path, {}, timeout=timeout)
        return True
    except XUIError:
        return False


def reset_client_traffic(base_url: str, api_token: str, email: str) -> bool:
    try:
        _request(base_url, api_token, "POST", f"/panel/api/clients/resetTraffic/{email}", {})
        return True
    except XUIError:
        return False


def get_client_traffic(base_url: str, api_token: str, email: str) -> dict:
    result = _request(base_url, api_token, "GET", f"/panel/api/clients/traffic/{email}")
    return result.get("obj") or {}


def get_client_links(base_url: str, api_token: str, email: str) -> list[str]:
    result = _request(base_url, api_token, "GET", f"/panel/api/clients/links/{email}")
    obj = result.get("obj", [])
    if isinstance(obj, list):
        return obj
    if isinstance(obj, str):
        return [obj] if obj else []
    return []


def compute_expiry_ms(duration_days: int, on_hold: bool = False, from_timestamp: int | None = None) -> int:
    """Compute expiryTime value for x-ui API — mirrors services/xui_client.py exactly."""
    if duration_days <= 0:
        return 0
    now = from_timestamp or int(time.time())
    if on_hold:
        return -duration_days * 86400000
    return (now + duration_days * 86400) * 1000


def generate_client_email(telegram_id: int, suffix: str = "") -> str:
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    base = f"u{telegram_id}_{rand}"
    return f"{base}{suffix}" if suffix else base


def generate_sub_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
