from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.liveness_agent import LivenessAgent
from utils.file_utils import FileUtils

router = APIRouter(
    prefix="/liveness",
    tags=["Liveness Detection"])

@router.post("/")
def liveness(
    aadhaar: UploadFile = File(...)):

    agent = LivenessAgent()

    aadhaar_path = FileUtils.save_upload(
        aadhaar)

    try:
        result = agent.run(
            aadhaar_path)

    except Exception as exc:

        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=str(exc))
    return result