# AI KYC Liveness Detection & Face Verification — Backend Deployment Guide

This document describes the backend deployment process on your Ubuntu/Debian server at IP **72.62.229.51** for the secure API domain **https://face-match-api.auremoai.site** (standard port 443).

To avoid port conflicts on your server, the local FastAPI server runs on port **8037** via Systemd, and Nginx reverse proxies port 443 SSL traffic to it.

---

## 1. Related Deployment Documents

* **Master Deployment Guide**: [deployment.md](deployment.md)
* **Frontend Web Dashboard**: [deployment-frontend.md](deployment-frontend.md)
* **Docker Infrastructure (LiveKit / Redis / Egress)**: [deployment-docker-services.md](deployment-docker-services.md)

---

## 2. Directory Structure & Paths

The backend files will be located at:
* **Project Directory**: `/var/www/html/face-match`
* **Python Virtual Environment**: `/var/www/html/face-match/.venv`
* **Data & SQLite Database Directory**: `/var/www/html/face-match/data`
* **Database File Path**: `/var/www/html/face-match/data/ekyc.db`
* **Uploaded Images Directory**: `/var/www/html/face-match/data/uploads`
* **InsightFace Model Directory**: `/var/www/html/face-match/data/.insightface`

---

## 3. Server Installation & Prerequisites

OpenCV, MediaPipe, and InsightFace require graphics-rendering system libraries. Install them alongside Python dependencies and Certbot:

```bash
sudo apt update
sudo apt install -y \
    nginx \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgles2 \
    libegl1 \
    sqlite3 \
    certbot \
    python3-certbot-nginx
```

---

## 4. Directory Setup

Create the workspace and backend data folders and assign proper ownership:

```bash
# Create main folder and data folder
sudo mkdir -p /var/www/html/face-match/data

# Set ownership and permissions
sudo chown -R $USER:www-data /var/www/html/face-match
sudo chmod -R 775 /var/www/html/face-match
```

---

## 5. Backend Environment & Dependency Setup

### A. Clone / Upload Repository
```bash
git clone <your-repository-url> /var/www/html/face-match
cd /var/www/html/face-match
```

### B. Python Setup
Configure the virtual environment and install dependencies:

```bash
cd /var/www/html/face-match
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### C. Configure Environment File (`.env`)
Copy the production environment template `.env.production` to `.env`:

```bash
cp /var/www/html/face-match/.env.production /var/www/html/face-match/.env
nano /var/www/html/face-match/.env
```

Ensure all keys and values are properly populated:

```env
# Directory for storing sqlite database and images
DATA_DIR=/var/www/html/face-match/data

# Redirect InsightFace model download to our writeable project data folder
INSIGHTFACE_HOME=/var/www/html/face-match/data/.insightface

# Allowed frontend origin (using standard HTTPS port)
ALLOWED_ORIGINS=https://face-match.auremoai.site

# Frontend Base URL (used for generating officer/customer video call links)
FRONTEND_BASE=https://face-match.auremoai.site

# LiveKit WebRTC Configuration (Production WSS Domain)
LIVEKIT_URL=wss://livekit.auremoai.site
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret1234567890abcdefghijklmnopx

# AWS S3 Storage Credentials (Required for LiveKit Egress recordings)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_S3_BUCKET=your-ekyc-recordings-bucket
AWS_S3_REGION=ap-south-1

# Gemini AI API Key (Used for Post-Call Sentiment & Fraud Video Analysis)
GEMINI_API_KEY=your_gemini_api_key
```

### D. Download MediaPipe Model Weights
The MediaPipe face landmarker model is a binary weight file (~5.7MB) ignored in Git. Download it on the server:

```bash
mkdir -p /var/www/html/face-match/models
wget -O /var/www/html/face-match/models/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
```

---

## 6. Systemd Service Setup

Create a systemd unit file to handle auto-starting and restarting the FastAPI backend on port **8037**:

```bash
sudo nano /etc/systemd/system/face-match-backend.service
```

Paste the following configuration:

```ini
[Unit]
Description=FastAPI eKYC Face Match Backend API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/html/face-match
EnvironmentFile=/var/www/html/face-match/.env
Environment="PATH=/var/www/html/face-match/.venv/bin"
ExecStart=/var/www/html/face-match/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8037 --workers 2
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable face-match-backend
sudo systemctl start face-match-backend
```

Check status:
```bash
sudo systemctl status face-match-backend
```

---

## 7. SSL Certificate Acquisition

Fetch the SSL certificate for your API domain using Certbot:

```bash
sudo certbot certonly --nginx -d face-match-api.auremoai.site
```

---

## 8. Nginx Server Configuration (HTTPS API Domain)

Create an Nginx configuration file for `face-match-api.auremoai.site`:

```bash
sudo nano /etc/nginx/sites-available/face-match-backend
```

Paste the following server block:

```nginx
server {
    listen 80;
    server_name face-match-api.auremoai.site;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name face-match-api.auremoai.site;

    # SSL Certificates (obtained via Certbot)
    ssl_certificate /etc/letsencrypt/live/face-match-api.auremoai.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/face-match-api.auremoai.site/privkey.pem;

    # Secure SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Set maximum upload size (vital for high-res Aadhaar/selfie submissions)
    client_max_body_size 20M;

    # Route all requests directly to FastAPI backend running on local port 8037
    location / {
        proxy_pass http://127.0.0.1:8037;
        proxy_http_version 1.1;

        # WebSocket and connection headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # Client IP propagation
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Handle preflight CORS requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://face-match.auremoai.site' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, DELETE, PUT' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
    }
}
```

Enable Nginx virtual host:

```bash
sudo ln -s /etc/nginx/sites-available/face-match-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 9. Redeploying Updates (When Backend Code Changes)

When code changes are pushed to git:

```bash
cd /var/www/html/face-match
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart face-match-backend
sudo journalctl -u face-match-backend -n 50 -f
```