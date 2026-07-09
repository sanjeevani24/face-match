# AI KYC Liveness Detection & Face Verification

## Overview

A full-stack, AI-powered eKYC verification system that performs passive liveness detection and face verification using computer vision and deep learning.

The system guides the user through randomized liveness challenges via a live browser camera feed, captures the highest-quality live frame, generates facial embeddings using InsightFace, and compares them against the Aadhaar photograph for identity verification — end to end, from a React frontend through to a FastAPI backend.

## Features

- Passive AI-based liveness detection, driven live from the browser camera
- Randomized challenge generation
  - Turn Left
  - Turn Right
  - Look Up
  - Blink Detection
- Face Mesh using MediaPipe
- Head Pose Estimation
- Eye Aspect Ratio (EAR) blink detection
- Automatic best-frame selection
- Face embedding using InsightFace (Buffalo_L)
- Face verification using cosine similarity
- Session-based liveness API — the browser streams captured frames one at a time; the backend tracks challenge progress and runs verification automatically once the sequence completes
- React (Vite + Tailwind) enterprise dashboard frontend with live camera capture, cross-browser `getUserMedia` handling, and a real-time challenge/progress UI
- REST API built with FastAPI
- Swagger UI documentation

## Project Structure

```
Face_match/
├── api/
│   ├── face_match.py
│   └── liveness.py
│
├── agents/
│   ├── crop_agent.py
│   ├── liveness_agent.py          # legacy local-webcam desktop demo (cv2.imshow)
│   ├── liveness_session.py        # session-based liveness used by the API
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
├── frontend/                      # React (Vite) dashboard + verification UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/            # Button, Card, Loader, ProgressBar
│   │   │   ├── layout/            # Sidebar, Header, DashboardLayout
│   │   │   ├── dashboard/         # Statistics, RecentVerification
│   │   │   └── verification/      # UploadCard, WebcamCard, ChallengeCard, StatusCard, ResultCard
│   │   ├── pages/                 # Dashboard, Verification, History
│   │   ├── services/              # api.js, verificationApi.js
│   │   ├── hooks/                 # useCamera.js
│   │   ├── context/               # VerificationContext.jsx
│   │   └── utils/                 # constants.js, media.js
│   ├── package.json
│   └── vite.config.js
│
├── main.py
│
├── requirements.txt
│
└── README.md
```

## Tech Stack

**Backend**: FastAPI, Uvicorn, OpenCV, MediaPipe, InsightFace, ONNX Runtime, Python

**Frontend**: React (Vite), Tailwind CSS v4, Axios, React Router, Lucide React, Framer Motion

## API Endpoints

### Face Match

`POST /face-match/`

Multipart form fields: `aadhaar` (file), `selfie` (file)

Compares an Aadhaar image against a selfie directly, outside of the liveness flow.

### Liveness Verification (session-based)

`POST /liveness/start`

Multipart form field: `aadhaar` (file)

Uploads the Aadhaar image once and starts a liveness session. Returns a `session_id` plus the first randomized challenge.

`POST /liveness/frame`

Multipart form fields: `session_id` (string), `frame` (file — one browser-captured frame)

Called repeatedly by the frontend (roughly every 300–400ms) while the challenge screen is active. Advances challenge state and, once all challenges are complete and a stable frame has been captured, runs face verification automatically. Example response, once finished:

```json
{
    "finished": true,
    "face_detected": true,
    "challenge": "LIVENESS VERIFIED",
    "challenge_index": 4,
    "challenge_total": 4,
    "progress": 100,
    "verification": {
        "verified": true,
        "similarity": 0.93,
        "confidence": "High"
    },
    "capture": "uploads/live_20260709_154210.png"
}
```

`DELETE /liveness/session/{session_id}`

Best-effort cleanup if the user leaves mid-session.

## Installation

Clone the repository:

```bash
git clone <repository_url>
cd Face_match
```

### Backend

Create and activate a virtual environment:

```bash
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL to your backend, e.g. http://localhost:8000
npm run dev
```

Open the printed local URL (typically http://localhost:5173). Camera access requires `https://` or `localhost`.

## Workflow

```
Upload Aadhaar (browser)
        │
        ▼
POST /liveness/start  →  session_id + first challenge
        │
        ▼
Browser streams captured frames  →  POST /liveness/frame
        │
        ▼
Random Challenge (Left / Right / Up / Blink)
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
Face Embedding (InsightFace)
        │
        ▼
Cosine Similarity
        │
        ▼
Identity Verification  →  returned in the final /liveness/frame response
```

## Future Improvements

- Passive anti-spoofing integration
- Face quality assessment
- Face alignment
- Adaptive similarity thresholds
- Multi-face detection
- Docker deployment
- Cloud deployment
- Authentication & role-based access
- Verification history & audit logs
- Complete KYC verification pipeline

## Author

Sanjeevani Chaurasia
B.Tech Artificial Intelligence & Data Science