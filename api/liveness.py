"""
api/liveness.py — replaces the old cv2.VideoCapture-based route.
... (existing docstring unchanged) ...
"""

import time
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from utils.file_utils import FileUtils
from agents.liveness_session import LivenessSession
from services.record_service import save_verification_record

router = APIRouter(
    prefix="/liveness",
    tags=["Liveness Detection"])

_sessions: dict[str, LivenessSession] = {}


@router.post("/start")
def start_liveness(aadhaar: UploadFile = File(...)):
    try:
        aadhaar_path = FileUtils.save_upload(aadhaar)
        session = LivenessSession(aadhaar_path)
    except Exception as exc:
        save_verification_record(
            source="liveness_session",
            decision="error",
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc))

    session_id = str(uuid.uuid4())
    _sessions[session_id] = session

    return {
        "session_id": session_id,
        "finished": False,
        "face_detected": False,
        "challenge": session.challenge.message(),
        "challenge_index": session.challenge.index + 1,
        "challenge_total": len(session.challenge.challenges),
        "progress": 0,
        "verification": None,
        "capture": None,
    }


@router.post("/frame")
async def liveness_frame(
    session_id: str = Form(...),
    frame: UploadFile = File(...)):
    session = _sessions.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown or expired session_id. Call /liveness/start first.")

    contents = await frame.read()
    np_bytes = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="Could not decode the uploaded frame.")

    try:
        result = session.process_frame(image)
    except Exception as exc:
        duration = time.time() - session.start_time
        save_verification_record(
            source="liveness_session",
            decision="error",
            duration_seconds=round(duration, 2),
            error_message=str(exc),
        )
        del _sessions[session_id]  # don't let a broken session linger
        raise HTTPException(status_code=400, detail=str(exc))

    if result["finished"]:
        # Verification already ran inside process_frame(); free the session.
        del _sessions[session_id]

    return result


@router.delete("/session/{session_id}")
def cancel_liveness_session(session_id: str):
    existed = _sessions.pop(session_id, None) is not None
    return {"cancelled": existed}