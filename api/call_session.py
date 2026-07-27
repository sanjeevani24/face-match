"""
api/call_session.py (self-hosted LiveKit version)

Officer-facing endpoints for a call-based verification session.
Swapped from Daily to a self-hosted LiveKit server -- see
services/livekit_client.py and services/livekit_bot.py, and
LIVEKIT_SETUP.md for how to run the server itself.

Flow, and why the customer route has two steps:
  1. POST /sessions -> creates the LiveKit room + officer token
     immediately, but the customer link only carries OUR OWN opaque
     secret (customer_link_token), not a LiveKit token.
  2. GET /join/{room_id}?link_token=... -> validates OUR secret, and
     only THEN mints a real LiveKit access token for the customer,
     lazily, right before they actually need it. This keeps the
     token's window tight and means our gating never depended on
     being able to decode LiveKit's own token format.

Runtime objects for an ACTIVE call (LiveKitCallBot, its frame queue,
the consumer thread) live in the in-memory _runtime registry -- not
the DB -- since they can't be serialized and a restart drops them
regardless.
"""

import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import livekit_client
from services import call_session_store as store
from services.livekit_bot import LiveKitCallBot
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
    aadhaar_path: str


class CreateSessionResponse(BaseModel):
    room_id: str
    officer_join_url: str
    customer_join_url: str


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest):
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


@router.get("/join/{room_id}")
def validate_customer_link(room_id: str, link_token: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")
    if session.customer_link_used:
        raise HTTPException(410, "This link has already been used")
    if link_token != session.customer_link_token:
        raise HTTPException(401, "Invalid link")

    # Gate passed -- NOW mint the real LiveKit token, short-lived, right
    # before the frontend actually needs it to join.
    customer_token = livekit_client.create_meeting_token(
        room_id, user_name=_customer_identity(room_id), is_owner=False, exp_seconds=1200
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
        bot.start_recording()

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