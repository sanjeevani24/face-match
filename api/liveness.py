"""
api/liveness.py — replaces the old cv2.VideoCapture-based route.

Old flow:  /liveness  -> LivenessAgent.run() opens the SERVER's own webcam
           in an infinite loop (cv2.VideoCapture + cv2.imshow). The frontend
           has no way to see or drive that loop.

New flow:  /liveness/start -> create a LivenessSession tied to the uploaded
                               Aadhaar image, return a session_id
           /liveness/frame -> the frontend posts ONE browser-captured frame
                               at a time; LivenessSession.process_frame()
                               advances challenge state and (once capture is
                               ready) runs face verification internally.
           /liveness/session/{id} -> DELETE to cancel/cleanup early.

LivenessAgent.run() and cv2.imshow/cv2.VideoCapture are no longer used by
the API at all. Keep liveness_agent.py around only if you still want the
old local-camera desktop demo; it's not called from here.
"""

import uuid

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from utils.file_utils import FileUtils
from agents.liveness_session import LivenessSession

router = APIRouter(
    prefix="/liveness",
    tags=["Liveness Detection"])

# In-memory session store. Fine for a single dev/uvicorn worker; move to
# Redis or a DB-backed store before running with multiple workers or behind
# a load balancer, since each worker would otherwise have its own dict.
_sessions: dict[str, LivenessSession] = {}


@router.post("/start")
def start_liveness(aadhaar: UploadFile = File(...)):
    """
    Upload the Aadhaar image once per verification attempt and get back a
    session_id. Every subsequent frame from the browser's camera is posted
    to /liveness/frame with this session_id.
    """
    aadhaar_path = FileUtils.save_upload(aadhaar)

    session = LivenessSession(aadhaar_path)
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
    """
    Post one frame captured from the browser's <video>/<canvas>. Returns the
    current challenge instruction, progress, and (once all challenges are
    completed and a stable frame is captured) the verification result —
    all in the same response, no extra round trip needed.
    """
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
        raise HTTPException(
            status_code=400,
            detail=str(exc))

    if result["finished"]:
        # Verification already ran inside process_frame(); free the session.
        del _sessions[session_id]

    return result


@router.delete("/session/{session_id}")
def cancel_liveness_session(session_id: str):
    """Called by the frontend if the user navigates away / restarts early."""
    existed = _sessions.pop(session_id, None) is not None
    return {"cancelled": existed}
