"""
services/livekit_client.py

Self-hosted LiveKit replacement for services/daily_client.py -- delete
that file once this is wired in, along with the DAILY_* env vars.
See LIVEKIT_SETUP.md for how to run the (free, self-hosted) server.

Env vars:
  LIVEKIT_URL          e.g. ws://localhost:7880  (wss://... in production)
  LIVEKIT_API_KEY
  LIVEKIT_API_SECRET

Key difference from Daily worth knowing: Daily gives each room its own
subdomain URL. LiveKit has ONE server URL and rooms are just names
within it -- so "room_url" throughout this codebase now means "the
LiveKit server's own URL", not a per-room address. Kept the field name
anyway so call_session.py and the frontend didn't need reshaping.

pip install livekit livekit-api
"""

import asyncio
import os
import uuid
from datetime import timedelta

from livekit import api

LIVEKIT_URL_DEFAULT = "ws://localhost:7880"


class LiveKitError(RuntimeError):
    pass


class ConfigError(LiveKitError):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"{name} is not set. Add it to your .env.")
    return value


def livekit_url() -> str:
    return os.environ.get("LIVEKIT_URL", LIVEKIT_URL_DEFAULT)


def _api_key() -> str:
    return _require_env("LIVEKIT_API_KEY")


def _api_secret() -> str:
    return _require_env("LIVEKIT_API_SECRET")


def _http_url() -> str:
    # LiveKitAPI (room service, Twirp) wants http(s), not ws(s) -- the
    # client SDKs are the ones that take the ws(s) URL directly.
    return livekit_url().replace("ws://", "http://").replace("wss://", "https://")


def create_room(applicant_id: str, exp_seconds: int = 3600) -> dict:
    """
    Sync wrapper (matches daily_client.create_room's sync signature, so
    call_session.py's create_session route doesn't need to become async).
    Rooms auto-create on first join, but creating explicitly lets us set
    empty_timeout -- LiveKit's rough equivalent of Daily's room `exp`.
    """
    room_name = f"ekyc-{applicant_id}-{uuid.uuid4().hex[:8]}"

    async def _create():
        lkapi = api.LiveKitAPI(_http_url(), api_key=_api_key(), api_secret=_api_secret())
        try:
            return await lkapi.room.create_room(
                api.CreateRoomRequest(name=room_name, empty_timeout=exp_seconds, max_participants=4)
            )
        finally:
            await lkapi.aclose()

    room = asyncio.run(_create())
    return {"name": room.name, "url": livekit_url()}


def delete_room(room_name: str) -> None:
    """Fire-and-forget cleanup, same role as daily_client.delete_room --
    optional given empty_timeout above already reclaims idle rooms."""
    async def _delete():
        lkapi = api.LiveKitAPI(_http_url(), api_key=_api_key(), api_secret=_api_secret())
        try:
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
        finally:
            await lkapi.aclose()

    try:
        asyncio.run(_delete())
    except Exception as exc:
        raise LiveKitError(f"delete_room failed: {exc}") from exc


def create_meeting_token(
    room_name: str,
    user_name: str,
    is_owner: bool = False,
    exp_seconds: int = 1800,
    hidden: bool = False,
) -> str:
    """
    Drop-in for daily_client.create_meeting_token. `user_name` is used
    as the LiveKit participant *identity* (not just a display name --
    it's how daily_bot/livekit_bot picks the customer's video track out
    of the room, so keep call sites passing the same identity strings
    they already do: f"officer-{room_id}", f"customer-{room_id}", etc.).

    is_owner grants room_admin (mute/remove others) -- same usage as
    the officer token in call_session.py.
    hidden=True is for the verification bot: it should subscribe to
    video but not appear as a visible participant to the humans on
    the call.
    """
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        room_admin=is_owner,
        can_publish=not hidden,
        can_subscribe=True,
        hidden=hidden,
    )
    token = (
        api.AccessToken(_api_key(), _api_secret())
        .with_identity(user_name)
        .with_grants(grants)
        .with_ttl(timedelta(seconds=exp_seconds))
    )
    return token.to_jwt()