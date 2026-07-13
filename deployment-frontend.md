# AI KYC Liveness Detection & Face Verification — Frontend Deployment Guide

This document describes the frontend deployment process on your Ubuntu/Debian server at IP **72.62.229.51** for the secure domain **https://face-match.auremoai.site:8036**.

---

## 1. Directory Structure & Paths

* **Repository Location**: `/var/www/html/face-match`
* **React Project Folder**: `/var/www/html/face-match/frontend`
* **Vite Build Output Folder**: `/var/www/html/face-match/frontend/dist`
* **Nginx Document Root**: `/var/www/html/face-match` (if copying files) or `/var/www/html/face-match/frontend/dist` (recommended for serving directly)

---

## 2. Server Installation & Prerequisites

To build the frontend, Node.js (v18+) is required. Install it along with Nginx and Certbot (for SSL certificates):

```bash
sudo apt update
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs nginx curl certbot python3-certbot-nginx
```

---

## 3. Environment Variable Configuration

Navigate to your frontend project directory:
```bash
cd /var/www/html/face-match/frontend
```

Create a production `.env` file:
```bash
nano /var/www/html/face-match/frontend/.env
```

Paste the following configurations. **Note that we explicitly point to the secure HTTPS backend API subdomain on port 8036**:
```env
# URL of the backend FastAPI service (using HTTPS)
VITE_API_URL=https://face-match-api.auremoai.site:8036

# Timeout for API requests (15 seconds)
VITE_API_TIMEOUT=15000
```

---

## 4. Build the React Frontend

Install the project dependencies and compile the production build:
```bash
cd /var/www/html/face-match/frontend
npm install
npm run build
```

This compiles your React code into static assets inside `/var/www/html/face-match/frontend/dist`.

### Optional: Move Build files to Document Root
If you want the compiled assets to reside exactly inside `/var/www/html/face-match`, copy the build folder contents:
```bash
# Copy compiled files to the main directory
cp -r /var/www/html/face-match/frontend/dist/* /var/www/html/face-match/
```

---

## 5. SSL Certificate Acquisition (CRITICAL)

Web browsers (Chrome, Safari, Firefox, Edge) strictly restrict camera permissions (`getUserMedia`) to **Secure Contexts** (`https://`). Without SSL, the webcam module will fail to start.

Run the following command to fetch your SSL certificate via Certbot:

```bash
sudo certbot certonly --nginx -d face-match.auremoai.site
```

---

## 6. Nginx Server Configuration (HTTPS Frontend Domain)

Create an Nginx configuration file to listen on port **8036** with SSL enabled for the domain **face-match.auremoai.site** and serve the static files.

### A. Create configuration file
```bash
sudo nano /etc/nginx/sites-available/face-match-frontend
```

Paste the following server block configuration (make sure to replace the SSL certificate path with yours if different):

```nginx
server {
    listen 8036 ssl;
    server_name face-match.auremoai.site;

    # SSL Certificates (obtained via Certbot)
    ssl_certificate /etc/letsencrypt/live/face-match.auremoai.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/face-match.auremoai.site/privkey.pem;

    # Secure SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Root directory containing static React assets
    # Point directly to frontend/dist or to the copied root path /var/www/html/face-match
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

### B. Enable Nginx Virtual Host
Create a symbolic link to activate this block, test configuration syntax, and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/face-match-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Redeploying Updates (When Frontend Code Changes)

When you push new frontend updates to your git repository, run these commands on the production server to build and deploy the changes:

```bash
# 1. Navigate to the frontend directory
cd /var/www/html/face-match/frontend

# 2. Pull the latest code changes
git pull origin main

# 3. Install packages (in case package.json dependencies changed)
npm install

# 4. Compile the production React build
npm run build

# 5. (If files are copied to the root path): Copy compiled files to /var/www/html/face-match
# cp -r dist/* /var/www/html/face-match/

# 6. Reload Nginx to ensure new files are picked up cleanly (optional)
sudo systemctl reload nginx
```
