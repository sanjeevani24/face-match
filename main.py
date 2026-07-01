from fastapi import APIRouter, UploadFile, File, FastAPI, HTTPException
import os
import shutil
from agents.face_match_agent import FaceMatchAgent

router = APIRouter()

agent = FaceMatchAgent()


@router.get("/")
def home():
    return {"message": "Face Match Agent Running"}


@router.post("/face-match")
def face_match(
    aadhaar: UploadFile = File(...),
    selfie: UploadFile = File(...)
):
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)

    aadhaar_fname = os.path.basename(aadhaar.filename)
    selfie_fname = os.path.basename(selfie.filename)

    aadhaar_path = os.path.join(uploads_dir, aadhaar_fname)
    selfie_path = os.path.join(uploads_dir, selfie_fname)

    with open(aadhaar_path, "wb") as buffer:
        shutil.copyfileobj(aadhaar.file, buffer)

    with open(selfie_path, "wb") as buffer:
        shutil.copyfileobj(selfie.file, buffer)

    try:
        result = agent.verify_face(
            aadhaar_path,
            selfie_path
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result


app = FastAPI(title="Face Match API")
app.include_router(router)

# Keep a compatibility alias so `uvicorn main:router` serves the FastAPI app
# instead of the raw APIRouter object.
router = app
