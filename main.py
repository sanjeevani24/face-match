from fastapi import FastAPI
from api.face_match import router as face_match_router
from api.liveness import router as liveness_router

app = FastAPI(
    title="AI KYC Verification API",
    version="1.0.0")

@app.get("/")
def home():
    return {"message": "AI KYC Verification API Running"}

app.include_router(face_match_router)

app.include_router(liveness_router)