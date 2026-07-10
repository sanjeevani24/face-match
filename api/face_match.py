from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.face_match_agent import FaceMatchAgent
from utils.file_utils import FileUtils
import time
from services.record_service import save_verification_record

router = APIRouter(
    prefix="/face-match",
    tags=["Face Match"])

agent = FaceMatchAgent()

STATUS_TO_DECISION = {
    "MATCH": "pass",
    "REVIEW": "review",
    "NO_MATCH": "fail",
    "REJECTED": "fail",
}

@router.post("/")
def face_match(aadhaar: UploadFile = File(...), selfie: UploadFile = File(...)):
    aadhaar_path = FileUtils.save_upload(aadhaar)
    selfie_path = FileUtils.save_upload(selfie)

    start = time.time()
    try:
        result = agent.verify_face(aadhaar_path, selfie_path)
    except Exception as exc:
        duration = time.time() - start
        save_verification_record(
            source="face_match_check",
            decision="error",
            duration_seconds=round(duration, 2),
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc))

    duration = time.time() - start
    save_verification_record(
        source="face_match_check",
        decision=STATUS_TO_DECISION.get(result.get("status"), "fail"),
        similarity=result.get("similarity_score"),
        confidence=None,
        duration_seconds=round(duration, 2),
    )

    return result