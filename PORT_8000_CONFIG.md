# Port 8000 Configuration Guide

## 🚀 Application Port Configuration

Your Market Scanner backend is configured to run on **port 8000** by default.

### **Current Configuration:**

```python
# main.py - Line 85
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### **Starting the Application:**

```bash
# Development mode (with auto-reload)
python main.py

# Production mode with uvicorn (RECOMMENDED)
uvicorn main:app --host 0.0.0.0 --port 8000

# Note: Avoid gunicorn with multiple workers for this app
# (causes SQLite conflicts and API rate limiting)
```

### **Health Check:**

```bash
# Local testing
curl http://localhost:8000/health

# Server testing
curl http://your-server-ip:8000/health

# Expected response:
{"status": "healthy", "timestamp": "2024-01-XX..."}
```

### **API Endpoints on Port 8000:**

- **Health**: `GET /health`
- **Authentication**: `POST /api/auth/login`, `POST /api/auth/register`
- **AI Assistant**: `POST /api/chat/message`, `GET /api/chat/recent`
- **Questionnaire**: `POST /api/questionnaire/save`, `GET /api/questionnaire`
- **Market Data**: `GET /api/market/*`

### **Firewall Configuration:**

```bash
# Ubuntu/Debian
sudo ufw allow 8000

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Check if port is open
sudo netstat -tlnp | grep :8000
```

### **Nginx Reverse Proxy (Optional):**

If you want to use port 80/443 with SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Environment Variables:**

Your `.env` file should include:

```bash
# CORS Configuration for port 8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://your-domain.com

# If using different port, update accordingly
```

### **Docker Configuration (if needed):**

```dockerfile
# Expose port 8000
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Systemd Service (Production):**

```ini
[Unit]
Description=Market Scanner API
After=network.target

[Service]
Type=exec
User=your-user
WorkingDirectory=/path/to/your/backend
Environment=PATH=/path/to/your/backend/venv/bin
ExecStart=/path/to/your/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## ✅ Port 8000 is Ready!

Your backend is configured and ready to run on port 8000. All documentation and scripts reference this port consistently.