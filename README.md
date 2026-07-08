AI KYC Liveness Detection & Face Verification

Overview
An AI-powered KYC verification system that performs passive liveness detection and face verification using computer vision and deep learning.

The system guides the user through randomized liveness challenges, captures the highest-quality live frame, generates facial embeddings using InsightFace, and compares them against the Aadhaar photograph for identity verification.

Features:

Passive AI-based Liveness Detection
Random Challenge Generation
Turn Left
Turn Right
Look Up
Blink Detection
Face Mesh using MediaPipe
Head Pose Estimation
Eye Aspect Ratio (EAR) Blink Detection
Automatic Best Frame Selection
Face Embedding using InsightFace (Buffalo_L)
Face Verification using Cosine Similarity
REST API built with FastAPI
Swagger UI Documentation

Project Structure:

Face_match/
├── api/
│   ├── face_match.py
│   └── liveness.py
│
├── agents/
│   ├── crop_agent.py
│   ├── liveness_agent.py
│   ├── verification_agent.py
│   └── antispoof_agent.py
│
├── services/
│
├── models/
│
├── utils/
│
├── uploads/
│
├── resources/
│
├── main.py
│
├── requirements.txt
│
└── README.md

Tech Stack:
Backend: FastAPI, Uvicorn
Computer Vision: OpenCV, MediaPipe
Face Recognition: InsightFace, ONNX Runtime
Language: Python

API Endpoints:

Face Match
POST /face-match

Compares Aadhaar image and selfie.

Liveness Verification
POST /liveness

Performs:

Liveness Detection
Best Frame Capture
Face Verification

Returns

{
    "status": "success",
    "liveness": true,
    "verification": {
        "verified": true,
        "similarity": 0.93,
        "confidence": "High"
    }
}

Installation:

Clone the repository:
git clone <repository_url>

cd Face_match

Create virtual environment:
python -m venv .venv

Activate:

Mac/Linux
source .venv/bin/activate

Windows
.venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Run:
uvicorn main:app --reload

Swagger:
http://127.0.0.1:8000/docs

Workflow:

Upload Aadhaar
        │
        ▼
Crop Aadhaar Photo
        │
        ▼
Start Camera
        │
        ▼
Random Challenge
        │
        ▼
Blink Detection
        │
        ▼
Head Pose Verification
        │
        ▼
Best Frame Selection
        │
        ▼
Face Embedding
        │
        ▼
Cosine Similarity
        │
        ▼
Identity Verification

Future Improvements:
Passive Anti-Spoofing Integration
Face Quality Assessment
Face Alignment
Adaptive Similarity Thresholds
Multi-face Detection
Docker Deployment
React Frontend
Cloud Deployment
Complete KYC Verification Pipeline

Author:
Sanjeevani Chaurasia
B.Tech Artificial Intelligence & Data Science
