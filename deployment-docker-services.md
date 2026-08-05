# AI KYC Infrastructure Services — Docker & LiveKit Deployment Guide

This document describes the deployment and lifecycle management of the infrastructure container stack (**Redis**, **LiveKit WebRTC Server**, and **LiveKit Egress Service**) using Docker Compose on your Ubuntu/Debian production server (**IP: 72.62.229.51**).

---

## 1. Overview & Architecture

The containerized stack provides real-time WebRTC audio/video communications and video call session recording for officer-customer KYC verifications:

```
                          ┌──────────────────────────┐
                          │   Nginx Reverse Proxy    │
                          │   (Port 443 SSL / HTTPS) │
                          └─────────────┬────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │ (wss://livekit...)         │ (https://face-match-api...)│
           ▼                            ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│   LiveKit Server     │    │   FastAPI Backend    │    │   React Frontend     │
│   (Port 7880 / 7881) │    │   (Systemd / 8037)   │    │   (Nginx / Static)   │
└──────────┬───────────┘    └──────────┬───────────┘    └──────────────────────┘
           │                           │
           │      ┌──────────────┐     │
           ├─────►│ Redis Server │◄────┤
           │      │ (Port 6379)  │     │
           │      └──────────────┘     │
           ▼                           ▼
┌──────────────────────────────────────────────────┐
│                LiveKit Egress                    │
│   (Room Composite Headless Recording -> AWS S3)  │
└──────────────────────────────────────────────────┘
```

---

## 2. Server Prerequisites & Docker Installation

If Docker and Docker Compose are not yet installed on your server, run the following setup script:

```bash
# Update packages and install Docker prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker’s official GPG key & repository
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose Plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker service and add user to docker group
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

*Note: Logout and log back in (or run `newgrp docker`) for group permissions to take effect.*

---

## 3. Network & Firewall Configuration (UFW)

LiveKit requires specific TCP and UDP ports open on your firewall and cloud security groups (AWS / DigitalOcean / Hetzner):

| Port / Protocol | Direction | Description |
| :--- | :--- | :--- |
| **80 / TCP** | Inbound | HTTP (Certbot & Nginx SSL Redirect) |
| **443 / TCP** | Inbound | HTTPS & WSS (Nginx Reverse Proxy) |
| **7880 / TCP** | Inbound | LiveKit HTTP / WebSocket Signaling |
| **7881 / TCP** | Inbound | LiveKit WebRTC RTC TCP fallback |
| **50000–50100 / UDP** | Inbound | LiveKit WebRTC Media Streams (RTP/RTCP) |

Configure UFW firewall on Ubuntu:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 7880/tcp
sudo ufw allow 7881/tcp
sudo ufw allow 50000:50100/udp
sudo ufw reload
```

---

## 4. Production Configuration Files

Ensure the following configuration files exist in your project directory (`/var/www/html/face-match`).

### A. `livekit.yaml`
Update `livekit.yaml` with your server's external IP address and production API keys:

```yaml
port: 7880
rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 50100
  use_external_ip: true

redis:
  address: redis:6379

keys:
  devkey: devsecret1234567890abcdefghijklmnopx
```

### B. `egress-config.yaml`
Ensure `egress-config.yaml` matches the API keys and Redis address:

```yaml
api_key: devkey
api_secret: devsecret1234567890abcdefghijklmnopx
ws_url: ws://livekit:7880
redis:
  address: redis:6379
```

### C. `docker-compose.yaml`
The standard composition defines Redis, LiveKit, and LiveKit Egress:

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"

  livekit:
    image: livekit/livekit-server
    restart: always
    command: --config /livekit.yaml
    ports:
      - "7880:7880"
      - "7881:7881"
      - "50000-50100:50000-50100/udp"
    volumes:
      - ./livekit.yaml:/livekit.yaml
    depends_on:
      - redis

  egress:
    image: livekit/egress
    restart: always
    environment:
      - EGRESS_CONFIG_FILE=/egress-config.yaml
    volumes:
      - ./egress-config.yaml:/egress-config.yaml
    depends_on:
      - redis
      - livekit
```

---

## 5. Starting the Infrastructure Services

Navigate to `/var/www/html/face-match` and launch the containers:

```bash
cd /var/www/html/face-match

# Start containers in background mode
docker compose up -d

# Verify container status
docker compose ps
```

To view live logs:
```bash
docker compose logs -f
```

---

## 6. Nginx SSL Setup for LiveKit (`livekit.auremoai.site`)

For WebRTC signaling over HTTPS from browsers, LiveKit needs a secure WebSocket domain (`wss://livekit.auremoai.site`).

### A. SSL Certificate Acquisition
```bash
sudo certbot certonly --nginx -d livekit.auremoai.site
```

### B. Create Nginx Configuration
Create `/etc/nginx/sites-available/livekit`:

```bash
sudo nano /etc/nginx/sites-available/livekit
```

Paste the following configuration:

```nginx
server {
    listen 80;
    server_name livekit.auremoai.site;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name livekit.auremoai.site;

    ssl_certificate /etc/letsencrypt/live/livekit.auremoai.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livekit.auremoai.site/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Maximum payload size for binary WebSocket framing
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:7880;
        proxy_http_version 1.1;

        # WebSocket Upgrade Headers (Crucial for WebRTC signaling)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings for long-lived WebSocket connections
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### C. Enable Site & Restart Nginx
```bash
sudo ln -s /etc/nginx/sites-available/livekit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Service Maintenance & Lifecycle Commands

| Task | Command |
| :--- | :--- |
| **Check Container Status** | `docker compose ps` |
| **Restart Services** | `docker compose restart` |
| **Stop Services** | `docker compose down` |
| **View LiveKit Logs** | `docker compose logs -f livekit` |
| **View Egress Logs** | `docker compose logs -f egress` |
| **Update Container Images** | `docker compose pull && docker compose up -d` |
