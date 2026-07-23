import os
import time
import uuid
import jwt
import requests


class HMSError(RuntimeError):
    pass


class ConfigError(HMSError):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(
            f"{name} is not set. Add it to your .env before using any "
            f"call-session endpoint (see services/.env.example)."
        )
    return value


def hms_access_key() -> str:
    return _require_env("HMS_ACCESS_KEY")


def hms_app_secret() -> str:
    return _require_env("HMS_APP_SECRET")


def hms_template_id() -> str:
    return _require_env("HMS_TEMPLATE_ID")


def hms_api_base() -> str:
    return os.environ.get("HMS_API_BASE", "https://api.100ms.live/v2")


def rtmp_ingest_base() -> str:
    return _require_env("RTMP_INGEST_BASE")


def recording_bot_join_url_base() -> str:
    return _require_env("RECORDING_BOT_JOIN_URL_BASE")


def _mgmt_token(expires_in: int = 300) -> str:
    now = int(time.time())
    payload = {
        "access_key": hms_access_key(),
        "type": "management",
        "version": 2,
        "iat": now,
        "nbf": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, hms_app_secret(), algorithm="HS256")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_mgmt_token()}", "Content-Type": "application/json"}


def create_room(applicant_id: str) -> dict:
    resp = requests.post(
        f"{hms_api_base()}/rooms",
        headers=_headers(),
        json={
            "name": f"ekyc-{applicant_id}-{uuid.uuid4().hex[:8]}",
            "template_id": hms_template_id(),
            "region": "in",
        },
        timeout=10,
    )
    if resp.status_code >= 300:
        raise HMSError(f"create_room failed: {resp.status_code} {resp.text}")
    return resp.json()


def generate_app_token(room_id: str, user_id: str, role: str, expires_in: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "access_key": hms_access_key(),
        "room_id": room_id,
        "user_id": user_id,
        "role": role,
        "type": "app",
        "version": 2,
        "iat": now,
        "nbf": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, hms_app_secret(), algorithm="HS256")


def start_recording(room_id: str) -> dict:
    resp = requests.post(
        f"{hms_api_base()}/recordings/room/{room_id}/start", headers=_headers(), json={}, timeout=10
    )
    if resp.status_code >= 300:
        raise HMSError(f"start_recording failed: {resp.status_code} {resp.text}")
    return resp.json()


def start_stream_tap(room_id: str, customer_join_token: str, officer_join_token: str) -> dict:
    """Starts the Beam bot: it silently joins as a muted 'recorder' role
    (configure this on your HMS_TEMPLATE_ID) and RTMP-pushes the room to
    a server you own. That feed is what services/stream_tap.py reads."""
    meeting_url = (
        f"{recording_bot_join_url_base()}?room_id={room_id}"
        f"&officer_token={officer_join_token}&customer_token={customer_join_token}"
    )
    rtmp_url = f"{rtmp_ingest_base()}/{room_id}"
    resp = requests.post(
        f"{hms_api_base()}/beam",
        headers=_headers(),
        json={
            "operation": "start",
            "room_id": room_id,
            "meeting_url": meeting_url,
            "rtmp_urls": [rtmp_url],
            "record": False,
            "resolution": {"width": 1280, "height": 720},
        },
        timeout=10,
    )
    if resp.status_code >= 300:
        raise HMSError(f"start_stream_tap failed: {resp.status_code} {resp.text}")
    return resp.json()


def stop_stream_tap(room_id: str) -> dict:
    resp = requests.post(
        f"{hms_api_base()}/beam",
        headers=_headers(),
        json={"operation": "stop", "room_id": room_id},
        timeout=10,
    )
    if resp.status_code >= 300:
        raise HMSError(f"stop_stream_tap failed: {resp.status_code} {resp.text}")
    return resp.json()