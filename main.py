from fastapi import FastAPI
from api.face_match import router as face_match_router
from api.liveness import router as liveness_router
from fastapi.middleware.cors import CORSMiddleware
from api.dashboard import router as dashboard_router
from models.db import init_db


app = FastAPI(
    title="AI KYC Verification API",
    version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def home():
    return {"message": "AI KYC Verification API Running"}

app.include_router(face_match_router)

app.include_router(liveness_router)

app.include_router(dashboard_router)
