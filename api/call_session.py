import asyncio
import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import hms_client
from services import call_session_store as store
from services.stream_tap import RoomStreamTap
from agents.live_call_session import LiveCallSession

router = APIRouter(prefix="/call", tags=["call-session"])

FRONTEND_BASE = os.environ.get("FRONTEND_BASE", "http://localhost:5173")


@dataclass
class _Runtime:
    stream_tap: Optional[RoomStreamTap] = None
    live_session: Optional[LiveCallSession] = None
    consumer_task: Optional[asyncio.Task] = None


_runtime: dict[str, _Runtime] = {}


class CreateSessionRequest(BaseModel):
    applicant_id: str
    aadhaar_path: str  # from your existing onboarding/upload flow (api/face_match.py)


class CreateSessionResponse(BaseModel):
    room_id: str
    officer_join_url: str
    customer_join_url: str


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest):
    room = hms_client.create_room(req.applicant_id)
    room_id = room["id"]

    officer_token = hms_client.generate_app_token(room_id, f"officer-{room_id}", "officer", 3600)
    customer_token = hms_client.generate_app_token(room_id, req.applicant_id, "customer", 1800)
    customer_jti = jwt.decode(customer_token, options={"verify_signature": False})["jti"]

    store.create_call_session(
        room_id=room_id,
        applicant_id=req.applicant_id,
        officer_token=officer_token,
        customer_token=customer_token,
        customer_jti=customer_jti,
        aadhaar_path=req.aadhaar_path,
    )

    return CreateSessionResponse(
        room_id=room_id,
        officer_join_url=f"{FRONTEND_BASE}/officer/call?room_id={room_id}&token={officer_token}",
        # Token-gated: single-use jti, short expiry, role-locked to this applicant.
        customer_join_url=f"{FRONTEND_BASE}/customer/call?room_id={room_id}&token={customer_token}",
    )


@router.get("/join/{room_id}")
def validate_customer_link(room_id: str, token: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")
    if session.customer_link_used:
        raise HTTPException(410, "This link has already been used")
    try:
        payload = jwt.decode(token, hms_client.hms_app_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(410, "This link has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    if payload.get("jti") != session.customer_jti or payload.get("role") != "customer":
        raise HTTPException(401, "Token does not match this session")
    return {"valid": True, "room_id": room_id, "applicant_id": session.applicant_id}


@router.post("/join/{room_id}/consume")
def consume_customer_link(room_id: str):
    """Call from the client the moment the 100ms SDK join actually
    succeeds -- not on page load -- so a refresh isn't punished but
    real reuse is blocked."""
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")
    store.mark_link_used(room_id)
    return {"ok": True}


async def _consume_frames(room_id: str, runtime: _Runtime):
    """Background task: RTMP tap -> Phase 3 processor."""
    while runtime.stream_tap is not None:
        sampled = await runtime.stream_tap.frame_queue.get()
        runtime.live_session.process_frame(sampled.image, sampled.ts)


@router.post("/sessions/{room_id}/start")
async def start_call_capture(room_id: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")

    recording = hms_client.start_recording(room_id)
    tap_result = hms_client.start_stream_tap(room_id, session.customer_token, session.officer_token)

    rtmp_read_url = f"{hms_client.rtmp_ingest_base()}/{room_id}"
    runtime = _Runtime(
        stream_tap=RoomStreamTap(room_id, rtmp_read_url),
        live_session=LiveCallSession(room_id, session.applicant_id, session.aadhaar_path),
    )
    _runtime[room_id] = runtime

    await runtime.stream_tap.start()
    runtime.consumer_task = asyncio.create_task(_consume_frames(room_id, runtime))

    store.mark_started(room_id)

    return {"recording": recording, "stream_tap": tap_result}


@router.get("/sessions/{room_id}/status")
def get_call_status(room_id: str):
    runtime = _runtime.get(room_id)
    if not runtime or not runtime.live_session:
        raise HTTPException(404, "Session not active")
    live = runtime.live_session
    return live.status(face_detected=live.consecutive_no_face == 0)


@router.post("/sessions/{room_id}/stop")
async def stop_call_capture(room_id: str):
    session = store.get_call_session(room_id)
    if not session:
        raise HTTPException(404, "Unknown session")

    runtime = _runtime.get(room_id)
    if runtime:
        if runtime.consumer_task:
            runtime.consumer_task.cancel()
        if runtime.stream_tap:
            await runtime.stream_tap.stop()

    hms_result = hms_client.stop_stream_tap(room_id)
    final = runtime.live_session.finalize() if runtime and runtime.live_session else None

    if final:
        store.mark_stopped(
            room_id,
            decision=final["decision"],
            identity_flagged=runtime.live_session.identity_flagged,
            spoof_flagged=runtime.live_session.spoof_flagged,
        )

    _runtime.pop(room_id, None)

    return {"stopped": hms_result, "result": final}