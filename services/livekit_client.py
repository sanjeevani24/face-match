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
    applicant_id = applicant_id.strip()
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

def start_room_recording(room_name: str, output_path: str) -> str:
    async def _start():
        lkapi = api.LiveKitAPI(_http_url(), api_key=_api_key(), api_secret=_api_secret())
        try:
            req = api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="speaker",
                audio_only=False,
                video_only=False,
                file_outputs=[
                    api.EncodedFileOutput(
                        file_type=api.EncodedFileType.MP4,
                        filepath=output_path,   # now just an S3 key, e.g. "recordings/{room_name}.mp4"
                        s3=api.S3Upload(
                            bucket=os.environ["AWS_S3_BUCKET"],
                            region=os.environ["AWS_S3_REGION"],
                            access_key=os.environ["AWS_ACCESS_KEY_ID"],
                            secret=os.environ["AWS_SECRET_ACCESS_KEY"],
                        ),
                    )
                ],
            )
            return await lkapi.egress.start_room_composite_egress(req)
        finally:
            await lkapi.aclose()

    res = asyncio.run(_start())
    return res.egress_id


def stop_room_recording(egress_id: str) -> None:
    async def _stop():
        lkapi = api.LiveKitAPI(_http_url(), api_key=_api_key(), api_secret=_api_secret())
        try:
            await lkapi.egress.stop_egress(api.StopEgressRequest(egress_id=egress_id))
        finally:
            await lkapi.aclose()

    asyncio.run(_stop())