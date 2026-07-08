from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.face_match_agent import FaceMatchAgent
from utils.file_utils import FileUtils

router = APIRouter(
    prefix="/face-match",
    tags=["Face Match"])

@router.post("/")
def face_match(
    aadhaar: UploadFile = File(...),
    selfie: UploadFile = File(...)):

    agent = FaceMatchAgent()

    aadhaar_path = FileUtils.save_upload(
        aadhaar)

    selfie_path = FileUtils.save_upload(
        selfie)

    try:
        result = agent.verify_face(
            aadhaar_path,
            selfie_path)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc))

    return result