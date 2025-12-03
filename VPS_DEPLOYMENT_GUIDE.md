# Piperlove Chess Engine API - RackNerd VPS Deployment Guide

**Complete deployment guide for running your chess engine API on a RackNerd VPS**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [VPS Specifications](#vps-specifications)
3. [Prerequisites](#prerequisites)
4. [Initial Server Setup](#initial-server-setup)
5. [Application Deployment](#application-deployment)
6. [Production Configuration](#production-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)
11. [Frontend Integration](#frontend-integration)

---

## 🎯 System Overview

### What You're Building

**Piperlove Chess Engine API** - A high-performance chess engine backend serving your GitHub Pages frontend (wwwtriplew.github.io).

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: wwwtriplew.github.io (GitHub Pages)                  │
│  - Static HTML/CSS/JS                                            │
│  - Chess UI with drag-and-drop gameplay                         │
│  - Makes API calls to backend                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTPS API Calls
                     │ (chess-engine.js)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: RackNerd VPS (Ubuntu 24.04)                           │
│  - FastAPI application (main.py)                                │
│  - Uvicorn ASGI server                                          │
│  - Nginx reverse proxy                                          │
│  - SSL/TLS encryption (Let's Encrypt)                           │
│  - Systemd service management                                   │
│                                                                  │
│  Chess Engine (src/):                                           │
│  - Bitboard-based move generation                               │
│  - Alpha-beta search with pruning                               │
│  - Transposition tables                                         │
│  - ~77,000+ NPS performance                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Current Setup (Before VPS):**
- Frontend: GitHub Pages at `https://wwwtriplew.github.io`
- Backend: Previously on Render/Vercel (free tier, cold starts)
- API Client: `assets/js/chess-engine.js` currently points to `https://pipier-love-api.vercel.app`

**Goal (After VPS Deployment):**
- Self-hosted API on your own domain/IP
- No cold starts, consistent performance
- Full control over resources and configuration

---

## 🖥️ VPS Specifications

**Your RackNerd VPS:**
- **OS:** Ubuntu 24.04 LTS (64-bit)
- **Memory:** 2.5 GB RAM
- **Disk:** 45 GB SSD
- **CPU:** Shared vCPU(s)
- **Network:** Unmetered bandwidth (likely 1 Gbps shared)

**Resource Requirements (Estimated):**
- **API Process:** ~100-300 MB RAM (idle/light load)
- **Peak Memory:** ~500 MB-1 GB (during complex searches)
- **Disk Usage:** ~500 MB for application + dependencies
- **CPU:** Moderate (chess engine is CPU-intensive during searches)

**Performance Expectations:**
- Can handle **10-50 concurrent users** with 2.5 GB RAM
- Search depth 8-10 plies with sub-1s response time
- ~77,000+ nodes per second (NPS) per engine instance

---

## ✅ Prerequisites

### Before You Begin

1. **SSH Access to Your VPS**
   - SSH key pair or root password
   - VPS IP address from RackNerd dashboard

2. **Domain Name (Recommended)**
   - Option A: Use existing domain (e.g., `api.wwwtriplew.me`)
   - Option B: Use VPS IP address directly (works but no SSL benefits)

3. **Tools on Your Local Machine**
   - SSH client (Terminal on Mac/Linux, PuTTY on Windows)
   - Text editor for config files
   - Git (for cloning repository)

### Domain Setup (If Using Custom Domain)

**Option 1: Subdomain (Recommended)**
```
api.wwwtriplew.me → VPS IP Address
```

**Option 2: Path-based (If wwwtriplew.me is elsewhere)**
```
wwwtriplew.me/api → VPS IP Address (reverse proxy needed)
```

**DNS Configuration:**
1. Log into your domain registrar (e.g., Namecheap, GoDaddy, Cloudflare)
2. Add an A record:
   - **Type:** A
   - **Name:** `api` (for api.wwwtriplew.me)
   - **Value:** Your VPS IP address
   - **TTL:** 300 seconds (5 minutes) for testing, 3600 (1 hour) for production
3. Wait 5-60 minutes for DNS propagation

**Verify DNS:**
```bash
# On your local machine
dig api.wwwtriplew.me
# or
nslookup api.wwwtriplew.me
```

---

## 🚀 Initial Server Setup

### Step 1: Connect to Your VPS

```bash
# Replace with your VPS IP address
ssh root@YOUR_VPS_IP

# If using SSH key:
ssh -i ~/.ssh/your_key root@YOUR_VPS_IP
```

### Step 2: Update System Packages

```bash
# Update package lists
apt update

# Upgrade installed packages
apt upgrade -y

# Install essential tools
apt install -y git curl wget vim htop ufw
```

### Step 3: Create Non-Root User (Security Best Practice)

```bash
# Create user 'piperlove' (or your preferred username)
adduser piperlove

# Add to sudo group
usermod -aG sudo piperlove

# Switch to new user
su - piperlove
```

**From now on, use this user for deployment.**

### Step 4: Configure Firewall

```bash
# Enable UFW firewall
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Check status
sudo ufw status
```

### Step 5: Install Python 3.11+

```bash
# Check Python version
python3 --version  # Should be 3.11+ on Ubuntu 24.04

# Install pip and venv
sudo apt install -y python3-pip python3-venv

# Install build tools (needed for some Python packages)
sudo apt install -y build-essential python3-dev
```

---

## 📦 Application Deployment

### Step 1: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/wwwtriplew/pipier_love_api.git

# Enter directory
cd pipier_love_api
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Install application dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi (>=0.104.0)
- uvicorn[standard] (>=0.24.0)
- pydantic (>=2.0.0)

### Step 4: Test Application Locally

```bash
# Test run (foreground, development mode)
uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, test the API:
curl http://YOUR_VPS_IP:8000/health
# Expected: {"status":"ok","engine":"ready"}
```

**Test move calculation:**
```bash
curl -X POST "http://YOUR_VPS_IP:8000/move" \
  -H "Content-Type: application/json" \
  -d '{
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "ai_thinking_ms": 2000
  }'
```

**Press `Ctrl+C` to stop the development server.**

---

## ⚙️ Production Configuration

### Step 1: Create Systemd Service

Create a systemd service file to run your API as a background service:

```bash
sudo nano /etc/systemd/system/piperlove-api.service
```

**Paste this configuration:**

```ini
[Unit]
Description=Piperlove Chess Engine API
After=network.target

[Service]
Type=simple
User=piperlove
Group=piperlove
WorkingDirectory=/home/piperlove/pipier_love_api
Environment="PATH=/home/piperlove/pipier_love_api/venv/bin"
ExecStart=/home/piperlove/pipier_love_api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2

# Restart policy
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=piperlove-api

[Install]
WantedBy=multi-user.target
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

**Key Configuration Notes:**
- `--host 127.0.0.1`: Only accept local connections (Nginx will reverse proxy)
- `--port 8000`: Internal port
- `--workers 2`: Run 2 worker processes (adjust based on CPU cores)
  - Rule of thumb: `(2 x num_cores) + 1`
  - For 1-2 vCPUs: 2-4 workers is reasonable
  - For your 2.5GB RAM: 2-3 workers is safe

### Step 2: Enable and Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable piperlove-api

# Start service
sudo systemctl start piperlove-api

# Check status
sudo systemctl status piperlove-api
```

**Expected output:**
```
● piperlove-api.service - Piperlove Chess Engine API
     Loaded: loaded (/etc/systemd/system/piperlove-api.service; enabled)
     Active: active (running) since ...
```

**Useful commands:**
```bash
# View logs
sudo journalctl -u piperlove-api -f

# Restart service
sudo systemctl restart piperlove-api

# Stop service
sudo systemctl stop piperlove-api
```

### Step 3: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Check if running
sudo systemctl status nginx
```

**Create Nginx configuration:**

```bash
sudo nano /etc/nginx/sites-available/piperlove-api
```

**Paste this configuration:**

```nginx
# Upstream backend (your FastAPI app)
upstream piperlove_backend {
    server 127.0.0.1:8000;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name api.wwwtriplew.me;  # Replace with your domain or IP

    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server (main configuration)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.wwwtriplew.me;  # Replace with your domain

    # SSL certificates (will be configured by Certbot)
    # ssl_certificate /etc/letsencrypt/live/api.wwwtriplew.me/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/api.wwwtriplew.me/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # CORS headers (allow your frontend)
    add_header Access-Control-Allow-Origin "https://wwwtriplew.github.io" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    add_header Access-Control-Allow-Credentials "true" always;

    # Handle OPTIONS preflight requests
    if ($request_method = OPTIONS) {
        add_header Access-Control-Allow-Origin "https://wwwtriplew.github.io";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        add_header Content-Length 0;
        add_header Content-Type text/plain;
        return 204;
    }

    # API endpoints
    location / {
        proxy_pass http://piperlove_backend;
        proxy_http_version 1.1;
        
        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (chess engine can take time)
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering off;
    }

    # Logging
    access_log /var/log/nginx/piperlove-api-access.log;
    error_log /var/log/nginx/piperlove-api-error.log;
}
```

**If using IP address instead of domain:**
- Replace `server_name api.wwwtriplew.me;` with `server_name YOUR_VPS_IP;`
- Skip the SSL sections (or use self-signed certificates)

**Enable the site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/piperlove-api /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 4: Test the Setup

```bash
# Test HTTP (should work now)
curl http://api.wwwtriplew.me/health
# or
curl http://YOUR_VPS_IP/health
```

---

## 🔒 SSL/HTTPS Setup

### Install Certbot (Let's Encrypt)

```bash
# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL Certificate

**For domain-based setup:**

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d api.wwwtriplew.me

# Or use webroot mode (if Nginx is running):
sudo certbot certonly --webroot -w /var/www/html -d api.wwwtriplew.me

# Start Nginx
sudo systemctl start nginx
```

**Follow prompts:**
1. Enter your email address
2. Agree to Terms of Service
3. Choose whether to share email with EFF (optional)

**Certificates will be saved to:**
```
/etc/letsencrypt/live/api.wwwtriplew.me/fullchain.pem
/etc/letsencrypt/live/api.wwwtriplew.me/privkey.pem
```

### Configure Nginx with SSL

The Nginx config above already has SSL directives commented out. Now uncomment them:

```bash
sudo nano /etc/nginx/sites-available/piperlove-api
```

**Uncomment these lines:**
```nginx
ssl_certificate /etc/letsencrypt/live/api.wwwtriplew.me/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.wwwtriplew.me/privkey.pem;
```

**Reload Nginx:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Test HTTPS

```bash
# Test HTTPS endpoint
curl https://api.wwwtriplew.me/health

# Test from browser (should show lock icon)
# Visit: https://api.wwwtriplew.me/health
```

### Auto-Renewal

Certbot automatically sets up a cron job for certificate renewal. Verify:

```bash
# Test renewal process (dry run)
sudo certbot renew --dry-run

# Renewal cron job is at:
# /etc/cron.d/certbot
```

Certificates auto-renew when they have 30 days or less remaining.

---

## 📊 Monitoring & Maintenance

### View Application Logs

```bash
# Follow logs in real-time
sudo journalctl -u piperlove-api -f

# View last 100 lines
sudo journalctl -u piperlove-api -n 100

# View logs from today
sudo journalctl -u piperlove-api --since today

# View errors only
sudo journalctl -u piperlove-api -p err
```

### Monitor System Resources

```bash
# Real-time monitoring
htop

# Disk usage
df -h

# Memory usage
free -h

# Check API process
ps aux | grep uvicorn
```

### Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/piperlove-api-access.log

# Error logs
sudo tail -f /var/log/nginx/piperlove-api-error.log
```

### Update Application

```bash
# Stop service
sudo systemctl stop piperlove-api

# Pull latest changes
cd ~/pipier_love_api
git pull origin main

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl start piperlove-api

# Check status
sudo systemctl status piperlove-api
```

### Backup Strategy

**1. Application Code:**
```bash
# Already backed up in Git, just push changes
cd ~/pipier_love_api
git add .
git commit -m "Update"
git push
```

**2. Configuration Files:**
```bash
# Backup systemd service
sudo cp /etc/systemd/system/piperlove-api.service ~/backups/

# Backup Nginx config
sudo cp /etc/nginx/sites-available/piperlove-api ~/backups/
```

**3. SSL Certificates:**
```bash
# Certificates are in /etc/letsencrypt/ (backed up during auto-renewal)
# To manually backup:
sudo tar -czf ~/backups/letsencrypt-backup.tar.gz /etc/letsencrypt/
```

---

## ⚡ Performance Optimization

### 1. Uvicorn Worker Tuning

Edit the systemd service file:

```bash
sudo nano /etc/systemd/system/piperlove-api.service
```

**Adjust workers:**
```ini
ExecStart=/home/piperlove/pipier_love_api/venv/bin/uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 3 \
  --worker-class uvicorn.workers.UvicornWorker \
  --limit-concurrency 100 \
  --backlog 2048
```

**Reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart piperlove-api
```

### 2. Enable Nginx Caching (Optional)

Add to Nginx config for static responses:

```nginx
# Add inside server block
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Increase System Limits

Edit limits for the piperlove user:

```bash
sudo nano /etc/security/limits.conf
```

**Add:**
```
piperlove soft nofile 65535
piperlove hard nofile 65535
```

**Reboot to apply:**
```bash
sudo reboot
```

### 4. Monitor Performance

Install and use monitoring tools:

```bash
# Install monitoring tools
sudo apt install -y sysstat iotop nethogs

# Monitor I/O
sudo iotop

# Monitor network
sudo nethogs

# System statistics
sar -u 1 10  # CPU usage every 1 second for 10 samples
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
sudo journalctl -u piperlove-api -n 50

# Common causes:
# - Port already in use
# - Permission issues
# - Python dependency errors

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Kill process if needed
sudo kill -9 <PID>
```

#### 2. CORS Errors from Frontend

**Frontend shows:** `Access-Control-Allow-Origin error`

**Fix in `main.py`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wwwtriplew.github.io",
        "https://www.wwwtriplew.github.io",
        "http://localhost:3000",  # For local testing
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)
```

**Or add in Nginx config** (already included above).

#### 3. Slow Response Times

**Possible causes:**
- Insufficient workers
- CPU overload
- Memory swapping

**Check:**
```bash
# CPU usage
top

# Memory usage (look for swap usage)
free -h

# If swap is being used heavily:
# - Reduce number of workers
# - Reduce transposition table size in search.py
```

#### 4. SSL Certificate Errors

```bash
# Check certificate status
sudo certbot certificates

# Renew manually if needed
sudo certbot renew

# Check Nginx SSL config
sudo nginx -t
```

#### 5. Cannot Connect to API

**Check firewall:**
```bash
sudo ufw status
# Ensure ports 80 and 443 are allowed
```

**Check Nginx:**
```bash
sudo systemctl status nginx
sudo nginx -t
```

**Check DNS:**
```bash
dig api.wwwtriplew.me
```

#### 6. High Memory Usage

**Check memory:**
```bash
free -h
ps aux --sort=-%mem | head -n 10
```

**Reduce memory usage:**
- Decrease workers in systemd service
- Reduce transposition table size in `src/search.py`:
  ```python
  # In main.py, change TT size
  tt = TranspositionTable(size_mb=32)  # Reduce from 64MB to 32MB
  ```

---

## 🌐 Frontend Integration

### Update Frontend API URL

**Edit `assets/js/chess-engine.js` in your frontend repo:**

```javascript
const ChessEngine = {
  // OLD: API_URL: 'https://pipier-love-api.vercel.app',
  API_URL: 'https://api.wwwtriplew.me',  // NEW: Your VPS domain
  
  // ... rest of code
}
```

**Commit and push:**
```bash
cd /path/to/wwwtriplew.github.io
git add assets/js/chess-engine.js
git commit -m "Update API URL to VPS"
git push
```

**GitHub Pages will auto-deploy in 1-2 minutes.**

### Test Frontend Integration

1. Visit `https://wwwtriplew.github.io/piperlove/play.html`
2. Make a move
3. Check browser console (F12) for API calls
4. Verify engine responds from your VPS

### Expected Console Output

```
🚀 Sending request to engine: thinking=8000ms, timeout=38000ms
📋 FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
✅ Response received: status=200
📥 Engine response: {move: "e2e4", score: 25, depth: 8, ...}
```

---

## 📈 Next Steps

### Optional Enhancements

**1. Add Rate Limiting:**
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure for API abuse prevention
```

**2. Set Up Monitoring Dashboard:**
```bash
# Install Prometheus + Grafana
# Or use simpler tools like Netdata
sudo apt install -y netdata
```

**3. Enable Automatic Backups:**
```bash
# Create backup script
nano ~/backup.sh
```

**4. Set Up Multiple Domains:**
```nginx
# Add more server_name entries in Nginx
server_name api.wwwtriplew.me chess-api.wwwtriplew.me;
```

**5. Implement API Key Authentication:**

Update `main.py`:
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/move", dependencies=[Depends(verify_api_key)])
async def calculate_move(request: MoveRequest):
    # ... existing code
```

---

## 📚 Additional Resources

### Documentation
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Uvicorn Docs:** https://www.uvicorn.org/
- **Nginx Docs:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **Systemd:** https://www.freedesktop.org/software/systemd/man/

### Useful Commands Reference

```bash
# Systemd service management
sudo systemctl start|stop|restart|status piperlove-api
sudo systemctl enable|disable piperlove-api
sudo journalctl -u piperlove-api -f

# Nginx management
sudo systemctl start|stop|restart|status nginx
sudo nginx -t
sudo nginx -s reload

# View logs
sudo journalctl -u piperlove-api -n 100
sudo tail -f /var/log/nginx/piperlove-api-access.log

# SSL certificate renewal
sudo certbot renew
sudo certbot certificates

# System monitoring
htop
df -h
free -h
```

---

## 🎉 Conclusion

You now have a fully functional, production-ready chess engine API running on your RackNerd VPS!

**What you've accomplished:**
- ✅ Deployed FastAPI application
- ✅ Configured systemd service for auto-start
- ✅ Set up Nginx reverse proxy
- ✅ Enabled SSL/HTTPS with Let's Encrypt
- ✅ Integrated with your GitHub Pages frontend
- ✅ Implemented proper security (firewall, SSL, CORS)
- ✅ Set up logging and monitoring

**Your API is now accessible at:**
- `https://api.wwwtriplew.me/health`
- `https://api.wwwtriplew.me/move` (POST)
- `https://api.wwwtriplew.me/docs` (API documentation)

**Performance Expectations:**
- No cold starts (always running)
- Consistent sub-1s response times
- ~77,000+ NPS
- Can handle 10-50 concurrent users

Enjoy your self-hosted chess engine! 🎮♟️

---

**Need Help?**
- Check logs: `sudo journalctl -u piperlove-api -f`
- Test API: `curl https://api.wwwtriplew.me/health`
- Verify DNS: `dig api.wwwtriplew.me`
- Monitor resources: `htop`

**Contact:**
- GitHub: @wwwtriplew
- Email: hello@wwwtriplew.me
