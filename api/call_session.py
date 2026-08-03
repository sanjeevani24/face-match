import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import livekit_client
from services import call_session_store as store
from services.livekit_bot import LiveKitCallBot
from services.transcription_service import transcribe_recording
from agents.live_call_session import LiveCallSession

router = APIRouter(prefix="/call", tags=["call-session"])

FRONTEND_BASE = os.environ.get("FRONTEND_BASE", "http://localhost:5173")


def _customer_identity(room_id: str) -> str:
    return f"customer-{room_id}"


@dataclass
class _Runtime:
    bot: Optional[LiveKitCallBot] = None
    live_session: Optional[LiveCallSession] = None
    consumer_thread: Optional[threading.Thread] = None
    stop_flag: threading.Event = field(default_factory=threading.Event)


_runtime: dict[str, _Runtime] = {}


class CreateSessionRequest(BaseModel):
    applicant_id: str
    aadhaar_path: Optional[str] = None

class CreateSessionResponse(BaseModel):
    room_id: str
    officer_join_url: str
    customer_join_url: str


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest):
    req.applicant_id = req.applicant_id.strip()

    print(repr(req.applicant_id))

    room = livekit_client.create_room(req.applicant_id, exp_seconds=3600)
    room_id = room["name"]
    room_url = room["url"]  # the LiveKit server's own URL -- see livekit_client.py

    officer_token = livekit_client.create_meeting_token(
        room_id, user_name=f"officer-{room_id}", is_owner=True, exp_seconds=3600
    )
    customer_link_token = uuid.uuid4().hex  # OUR secret -- not a LiveKit token

    store.create_call_session(
        room_id=room_id,
        room_url=room_url,
        applicant_id=req.applicant_id,
        officer_meeting_token=officer_token,
        customer_link_token=customer_link_token,
        aadhaar_path=req.aadhaar_path,
    )

    officer_params = urlencode({"room_id": room_id, "room_url": room_url, "token": officer_token})
    customer_params = urlencode({"room_id": room_id, "link_token": customer_link_token})

    return CreateSessionResponse(
        room_id=room_id,
        officer_join_url=f"{FRONTEND_BASE}/officer/call?{officer_params}",
        customer_join_url=f"{FRONTEND_BASE}/customer/call?{customer_params}",
    )


from datetime import datetime, timezone

RECONNECT_WINDOW_SECONDS = 180

@router.get("/join/{room_id}")
def validate_customer_link(room_id: str, link_token: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")
    if link_token != session.customer_link_token:
        raise HTTPException(401, "Invalid link")

    if session.customer_link_used_at is not None:
        # SQLite drops timezone info on round-trip (it has no native
        # tz-aware datetime type), so customer_link_used_at always
        # comes back naive regardless of how it was written. Compare
        # using naive UTC on both sides rather than fighting SQLite.
        now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        elapsed = (now_naive_utc - session.customer_link_used_at).total_seconds()
        if elapsed > RECONNECT_WINDOW_SECONDS:
            raise HTTPException(410, "This link has expired and can no longer be used to reconnect")

    customer_token = livekit_client.create_meeting_token(
        room_id, user_name=_customer_identity(room_id), is_owner=False, exp_seconds=7200
    )

    return {
        "valid": True,
        "room_id": room_id,
        "room_url": session.room_url,
        "applicant_id": session.applicant_id,
        "meeting_token": customer_token,
    }


@router.post("/join/{room_id}/consume")
def consume_customer_link(room_id: str):
    """Call from the client the moment the LiveKit SDK join actually
    succeeds -- not on page load -- so a refresh isn't punished but
    real reuse is blocked."""
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")
    store.mark_link_used(room_id)
    return {"ok": True}


def _consume_frames(room_id: str, runtime: "_Runtime"):
    """Runs in its own thread -- bot.frame_queue is a plain thread-safe
    queue.Queue, so this is a normal blocking loop, not asyncio. Unchanged
    from the Daily version: livekit_bot.py bridges its asyncio frame
    stream into this same queue shape."""
    while not runtime.stop_flag.is_set():
        try:
            ts, frame = runtime.bot.frame_queue.get(timeout=0.5)
        except Exception:
            continue
        print(f"[CALL {room_id}] dequeued frame, shape={frame.shape}")   #<----- debug print line
        runtime.live_session.process_frame(frame, ts)


@router.post("/sessions/{room_id}/start")
def start_call_capture(room_id: str, enable_recording: bool = False):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")

    bot_token = livekit_client.create_meeting_token(
        room_id, user_name="verification-bot", is_owner=True, exp_seconds=3600, hidden=True
    )
    bot = LiveKitCallBot(
        livekit_url=session.room_url,
        bot_token=bot_token,
        customer_identity=_customer_identity(room_id),
    )
    bot.join()
    if not bot.wait_until_joined(timeout=10.0):
        raise HTTPException(504, "Bot did not join the room in time")

    if enable_recording:
        # See LiveKitCallBot.start_recording's docstring -- no-op until
        # Egress is wired up; self-hosted --dev mode doesn't include it.
        bot.start_recording(room_id)

    live_session = LiveCallSession(room_id, session.applicant_id, session.aadhaar_path)

    runtime = _Runtime(bot=bot, live_session=live_session)
    runtime.consumer_thread = threading.Thread(
        target=_consume_frames, args=(room_id, runtime), daemon=True
    )
    runtime.consumer_thread.start()
    _runtime[room_id] = runtime

    store.mark_started(room_id)

    return {"joined": True, "recording": enable_recording}


@router.get("/sessions/{room_id}/status")
def get_call_status(room_id: str):
    runtime = _runtime.get(room_id)
    if not runtime or not runtime.live_session:
        raise HTTPException(404, "Session not active")
    live = runtime.live_session
    return live.status(face_detected=live.consecutive_no_face == 0)


@router.post("/sessions/{room_id}/stop")
def stop_call_capture(room_id: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")

    runtime = _runtime.get(room_id)
    final = None
    if runtime:
        runtime.stop_flag.set()
        if runtime.consumer_thread:
            runtime.consumer_thread.join(timeout=5.0)
        if runtime.bot:
            runtime.bot.stop_recording()
            runtime.bot.leave()
        if runtime.live_session:
            final = runtime.live_session.finalize()

    if final:
        store.mark_stopped(
            room_id,
            decision=final["decision"],
            identity_flagged=runtime.live_session.identity_flagged,
            spoof_flagged=runtime.live_session.spoof_flagged,
        )

    _runtime.pop(room_id, None)
    # Relying on the room's empty_timeout (set at creation) rather than
    # deleting here immediately -- avoids a race with any last-moment
    # media flush.

    return {"stopped": True, "result": final}

# separate from _runtime — recording has its own lifecycle now
_egress_sessions: dict[str, str] = {}   # room_id -> egress_id

@router.post("/sessions/{room_id}/recording/start")
def start_recording(room_id: str):
    if room_id in _egress_sessions:
        raise HTTPException(400, "Recording already in progress for this room")
    output_path = f"/out/{room_id}.mp4"
    try:
        egress_id = livekit_client.start_room_recording(room_id, output_path)
    except Exception as exc:
        raise HTTPException(500, f"Failed to start recording: {exc}")
    _egress_sessions[room_id] = egress_id
    return {"recording": True, "egress_id": egress_id}

@router.post("/sessions/{room_id}/recording/stop")
def stop_recording(room_id: str):
    egress_id = _egress_sessions.pop(room_id, None)
    if not egress_id:
        raise HTTPException(404, "No active recording for this room")
    livekit_client.stop_room_recording(egress_id)
    return {"recording": False}


@router.post("/sessions/{room_id}/transcript")
def get_transcript(room_id: str):
    try:
        return transcribe_recording(room_id)
    except Exception as exc:
        raise HTTPException(500, f"Failed to transcribe recording: {exc}")