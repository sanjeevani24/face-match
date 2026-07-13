# AI KYC Liveness Detection & Face Verification — Backend Deployment Guide

This document describes the backend deployment process on your Ubuntu/Debian server at IP **72.62.229.51** for the API domain **face-match-api.auremoai.site** on port **8036**.

---

## 1. Directory Structure & Paths

The backend files will be located at:
* **Project Directory**: `/var/www/html/face-match`
* **Python Virtual Environment**: `/var/www/html/face-match/.venv`
* **Data & SQLite Database Directory**: `/var/www/html/face-match/data`
* **Database File Path**: `/var/www/html/face-match/data/ekyc.db`
* **Uploaded Images Directory**: `/var/www/html/face-match/data/uploads`

---

## 2. Server Installation & Prerequisites

OpenCV, MediaPipe, and InsightFace require graphics-rendering libraries. Install them alongside Python dependencies:

```bash
sudo apt update
sudo apt install -y \
    nginx \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    sqlite3
```

---

## 3. Directory Setup

Create the workspace and backend data folders and assign permissions to both the deployer and the `www-data` group:

```bash
# Create main folder and data folder
sudo mkdir -p /var/www/html/face-match/data

# Set ownership and permissions
sudo chown -R $USER:www-data /var/www/html/face-match
sudo chmod -R 775 /var/www/html/face-match
```

---

## 4. Backend Environment & Dependency Setup

### A. Clone/Upload Files
Upload your files to `/var/www/html/face-match` or clone them:
```bash
# If using git:
git clone <your-repository-url> /var/www/html/face-match
```

### B. Python Setup
Configure the virtual environment and install the required modules:
```bash
cd /var/www/html/face-match
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### C. Configure `.env` File
Create a `.env` file at `/var/www/html/face-match/.env` to configure your environment variables:
```bash
nano /var/www/html/face-match/.env
```

Add the following configurations:
```env
# Directory for storing sqlite database and images
DATA_DIR=/var/www/html/face-match/data

# Allowed frontend origin (cross-origin request allowed from your frontend domain)
ALLOWED_ORIGINS=http://face-match.auremoai.site:8036,https://face-match.auremoai.site:8036
```

---

## 5. Systemd Service Setup

Create a systemd unit file to handle the automatic starting and restarting of the FastAPI backend application on port **8000** locally.

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
ExecStart=/var/www/html/face-match/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable face-match-backend
sudo systemctl start face-match-backend
```

To view backend service logs:
```bash
sudo journalctl -u face-match-backend -f
```

---

## 6. Nginx Server Configuration (API Domain)

Create an Nginx configuration file to listen on port **8036** for the domain **face-match-api.auremoai.site** and proxy it to the local port **8000**.

### A. Create configuration file
```bash
sudo nano /etc/nginx/sites-available/face-match-backend
```

Paste the following server block config:

```nginx
server {
    listen 8036;
    server_name face-match-api.auremoai.site;

    # Set maximum upload size (vital for image submissions)
    client_max_body_size 20M;

    # Route all requests directly to FastAPI backend running on local port 8000
    location / {
        proxy_pass http://127.0.0.1:8000;
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

        # Handle preflight CORS requests if needed (FastAPI handles it as well)
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'http://face-match.auremoai.site:8036' always;
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

### B. Enable Nginx Virtual Host
Link the configuration and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/face-match-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Redeploying Updates (When Backend Code Changes)

When you push new backend updates to your git repository, run these commands on the production server to deploy the changes:

```bash
# 1. Navigate to the project directory
cd /var/www/html/face-match

# 2. Pull the latest code changes
git pull origin main

# 3. Activate venv & update Python dependencies (in case requirements.txt was updated)
source .venv/bin/activate
pip install -r requirements.txt

# 4. Restart the FastAPI Systemd service to load new code
sudo systemctl restart face-match-backend

# 5. (Optional) Verify that the service restarted successfully and monitor logs
sudo systemctl status face-match-backend
sudo journalctl -u face-match-backend -n 50 -f
```
