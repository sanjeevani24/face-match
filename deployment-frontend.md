# AI KYC Liveness Detection & Face Verification — Frontend Deployment Guide

This document describes the frontend deployment process on your Ubuntu/Debian server at IP **72.62.229.51** for the secure domain **https://face-match.auremoai.site** (standard port 443).

---

## 1. Related Deployment Documents

* **Master Deployment Guide**: [deployment.md](deployment.md)
* **Backend API Deployment**: [deployment-backend.md](deployment-backend.md)
* **Docker Infrastructure (LiveKit / Redis / Egress)**: [deployment-docker-services.md](deployment-docker-services.md)

---

## 2. Directory Structure & Paths

* **Repository Location**: `/var/www/html/face-match`
* **React Project Folder**: `/var/www/html/face-match/frontend`
* **Vite Build Output Folder**: `/var/www/html/face-match/frontend/dist`
* **Nginx Document Root**: `/var/www/html/face-match/frontend/dist`

---

## 3. Server Installation & Prerequisites

To build the frontend, Node.js (v18+) is required. Install it along with Nginx and Certbot:

```bash
sudo apt update
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs nginx curl certbot python3-certbot-nginx
```

---

## 4. Environment Variable Configuration

Navigate to your frontend project directory:

```bash
cd /var/www/html/face-match/frontend
```

Copy the production environment template `.env.production` to `.env`:

```bash
cp .env.production .env
nano .env
```

Verify your frontend `.env` contains the following settings:

```env
# Base URL of the HTTPS FastAPI backend API (no trailing slash)
VITE_API_URL=https://face-match-api.auremoai.site

# API Request timeout in milliseconds (15 seconds default)
VITE_API_TIMEOUT=15000

# LiveKit WebRTC Server Secure WebSocket URL (Nginx SSL proxy)
VITE_LIVEKIT_URL=wss://livekit.auremoai.site
```

---

## 5. Build the React Frontend

Install project dependencies and compile the production bundle:

```bash
cd /var/www/html/face-match/frontend
npm install
npm run build
```

This compiles your React application into static production assets inside `/var/www/html/face-match/frontend/dist`.

---

## 6. SSL Certificate Acquisition (CRITICAL)

Web browsers (Chrome, Safari, Firefox, Edge) strictly restrict camera permissions (`getUserMedia`) to **Secure Contexts** (`https://`). Without SSL, the webcam module and LiveKit video stream will fail to initialize.

Fetch your SSL certificate via Certbot:

```bash
sudo certbot certonly --nginx -d face-match.auremoai.site
```

---

## 7. Nginx Server Configuration (HTTPS Frontend Domain)

Create an Nginx server block configuration:

```bash
sudo nano /etc/nginx/sites-available/face-match-frontend
```

Paste the following configuration:

```nginx
server {
    listen 80;
    server_name face-match.auremoai.site;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name face-match.auremoai.site;

    # SSL Certificates (obtained via Certbot)
    ssl_certificate /etc/letsencrypt/live/face-match.auremoai.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/face-match.auremoai.site/privkey.pem;

    # Secure SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Root directory pointing to static Vite build output
    root /var/www/html/face-match/frontend/dist;
    index index.html;

    # Handle React client-side routing (redirect missing routes to index.html)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Enable gzip compression for optimized file delivery
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

Enable virtual host & restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/face-match-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. Redeploying Updates (When Frontend Code Changes)

When frontend code updates are pushed to git:

```bash
# 1. Navigate to frontend directory
cd /var/www/html/face-match/frontend

# 2. Pull latest code
git pull origin main

# 3. Ensure production .env exists
cp .env.production .env

# 4. Install dependencies & rebuild React application
npm install
npm run build

# 5. Reload Nginx
sudo systemctl reload nginx
```