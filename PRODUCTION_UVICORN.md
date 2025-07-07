# Production Deployment with Uvicorn

## 🚀 Why Uvicorn for Production?

For this Market Scanner application, **uvicorn is the recommended production server** instead of gunicorn with multiple workers because:

### **Issues with Gunicorn + Multiple Workers:**
- ❌ **SQLite Database Conflicts**: Multiple workers trying to write to the same SQLite database
- ❌ **API Rate Limiting**: 4 workers = 4x API calls = hitting rate limits faster
- ❌ **Background Task Duplication**: Each worker runs background tasks independently
- ❌ **Resource Waste**: Unnecessary overhead for this application's workload

### **Benefits of Single Uvicorn Process:**
- ✅ **No Database Conflicts**: Single process, single database connection
- ✅ **Controlled API Usage**: Single background task scheduler
- ✅ **Efficient Resource Usage**: Optimal for this application's async nature
- ✅ **Simpler Deployment**: Easier to monitor and debug

## 🔧 Production Configuration

### **Recommended Production Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### **With Additional Production Options:**
```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --access-log \
  --log-level info
```

### **Environment Variables for Production:**
```bash
# In your .env file
FULLY_DILUTED_UPDATE_INTERVAL=1800  # 30 minutes
MARKET_ANALYSIS_UPDATE_INTERVAL=2700  # 45 minutes
LOG_LEVEL=INFO
DEBUG=false
```

## 🛡️ Production Systemd Service

Create `/etc/systemd/system/market-scanner.service`:

```ini
[Unit]
Description=Market Scanner API
After=network.target

[Service]
Type=exec
User=pi
Group=pi
WorkingDirectory=/home/pi/Documents/EverBloom/backend
Environment=PATH=/home/pi/Documents/EverBloom/backend/venv/bin
ExecStart=/home/pi/Documents/EverBloom/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/pi/Documents/EverBloom/backend/data
ReadWritePaths=/home/pi/Documents/EverBloom/backend/logs

[Install]
WantedBy=multi-user.target
```

### **Enable and Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable market-scanner
sudo systemctl start market-scanner
sudo systemctl status market-scanner
```

## 📊 Monitoring and Logs

### **Check Service Status:**
```bash
sudo systemctl status market-scanner
```

### **View Logs:**
```bash
# Real-time logs
sudo journalctl -u market-scanner -f

# Recent logs
sudo journalctl -u market-scanner --since "1 hour ago"
```

### **Application Logs:**
```bash
# Check application logs
tail -f /home/pi/Documents/EverBloom/backend/logs/app.log
```

## 🔍 Health Monitoring

### **Health Check Script:**
```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### **Automated Health Monitoring (Cron):**
```bash
# Add to crontab: crontab -e
*/5 * * * * /home/pi/health_check.sh >> /var/log/market-scanner-health.log 2>&1
```

## 🚨 Troubleshooting

### **Common Issues:**

1. **Rate Limiting (429 errors):**
   ```bash
   # Increase intervals in .env
   FULLY_DILUTED_UPDATE_INTERVAL=3600  # 1 hour
   MARKET_ANALYSIS_UPDATE_INTERVAL=5400  # 1.5 hours
   ```

2. **Database Permission Errors:**
   ```bash
   # Fix file permissions
   chmod 755 /home/pi/Documents/EverBloom/backend/data
   chmod 644 /home/pi/Documents/EverBloom/backend/data/*.db
   ```

3. **Service Won't Start:**
   ```bash
   # Check logs
   sudo journalctl -u market-scanner --no-pager
   
   # Test manually
   cd /home/pi/Documents/EverBloom/backend
   source venv/bin/activate
   python main.py
   ```

## 🎯 Performance Optimization

### **For High Traffic (if needed):**
If you need to scale beyond single uvicorn process:

1. **Use Nginx Load Balancer** with multiple uvicorn instances on different ports
2. **Separate Database** (PostgreSQL instead of SQLite)
3. **Redis for Caching** to reduce API calls

### **Current Setup is Optimal For:**
- Small to medium traffic
- SQLite database
- Background data fetching
- Single server deployment

## ✅ Production Checklist

- [ ] Use single uvicorn worker
- [ ] Set conservative API intervals
- [ ] Configure systemd service
- [ ] Set up log monitoring
- [ ] Configure health checks
- [ ] Secure file permissions
- [ ] Test restart behavior

Your application is now optimized for production with uvicorn!