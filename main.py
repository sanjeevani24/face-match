from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from api.face_match import router as face_match_router
from api.liveness import router as liveness_router
from api.dashboard import router as dashboard_router
from api.call_session import router as call_session_router
from fastapi.middleware.cors import CORSMiddleware
from models.db import init_db

app = FastAPI(
    title="AI KYC Verification API",
    version="1.0.0")

allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(call_session_router)