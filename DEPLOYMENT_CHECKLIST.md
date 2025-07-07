# Backend Deployment Checklist

## ✅ Database Initialization Status

### **FIXED ISSUES:**
1. **✅ `trade_questions` table creation** - Added to `ai_assistant_db.py` initialization
2. **✅ Database auto-creation** - All databases will be created automatically on startup
3. **✅ Directory creation** - Database directories are created automatically

### **Database Files Created on Startup:**
- `./data/users.db` - User accounts and email whitelist
- `./data/ai_assistant.db` - Chat sessions, messages, and questionnaire data

## 🔧 Pre-Deployment Setup

### 1. Environment Configuration
```bash
# Copy and configure environment file
cp .env.example .env

# Edit .env with your production values:
# - JWT_SECRET_KEY (generate a strong random key)
# - GEMINI_API_KEY (your Google Gemini API key)
# - CORS_ORIGINS (your frontend domain)
# - Database paths (optional, defaults are fine)
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Initial User Setup
```bash
# Add your email to whitelist
python admin_tools.py add-email your-email@domain.com

# Create your admin user account
python admin_tools.py create-user your-email@domain.com --name "Your Name"

# Test login
python admin_tools.py test-login your-email@domain.com
```

## 🚀 Deployment Steps

### 1. Server Setup
- Ensure Python 3.8+ is installed
- Create application directory
- Set up reverse proxy (nginx/apache) if needed
- Configure firewall for port 8000

### 2. Application Deployment
```bash
# Clone/upload your code
# Install dependencies (see above)
# Configure environment variables
# Set up systemd service (optional)
```

### 3. Database Verification
```bash
# Verify databases are created
ls -la data/
# Should show: users.db, ai_assistant.db

# Check table creation
python -c "
from app.services.user_db import user_db
from app.services.ai_assistant_db import ai_assistant_db
print('✅ Databases initialized successfully')
"
```

### 4. Start Application
```bash
# Development
python main.py

# Production with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000

# Or with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔍 Post-Deployment Verification

### 1. Health Check
```bash
curl http://your-server:8000/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### 2. Database Functionality
```bash
# List users
python admin_tools.py list-users

# Test questionnaire endpoints
curl -X GET http://your-server:8000/api/questionnaire \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. AI Assistant Test
```bash
# Test chat creation (requires valid JWT token)
curl -X POST http://your-server:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "Hello", "status": "pre-trade"}'
```

## 🛡️ Security Considerations

### 1. Environment Variables
- **JWT_SECRET_KEY**: Use a strong, random 256-bit key
- **GEMINI_API_KEY**: Keep secure, don't log or expose
- **Database files**: Ensure proper file permissions (600)

### 2. CORS Configuration
- Set `CORS_ORIGINS` to your actual frontend domain(s)
- Don't use wildcard (*) in production

### 3. File Permissions
```bash
# Secure database directory
chmod 700 data/
chmod 600 data/*.db
```

## 📊 Monitoring & Maintenance

### 1. Log Files
- Check `logs/` directory for application logs
- Monitor for database errors or connection issues

### 2. Database Backups
```bash
# Backup databases
cp data/users.db backups/users_$(date +%Y%m%d).db
cp data/ai_assistant.db backups/ai_assistant_$(date +%Y%m%d).db
```

### 3. User Management
```bash
# Regular admin tasks
python admin_tools.py list-users
python admin_tools.py list-whitelist
```

## 🚨 Troubleshooting

### Common Issues:

1. **Database Permission Errors**
   ```bash
   # Fix permissions
   chmod 755 data/
   chmod 644 data/*.db
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

3. **JWT Token Issues**
   ```bash
   # Verify JWT secret is set
   python -c "from app.core.config import settings; print('JWT configured:', bool(settings.jwt_secret_key))"
   ```

4. **Gemini API Issues**
   ```bash
   # Test API key
   python -c "from app.services.ai_assistant_service import _require_client; print('✅ Gemini client OK' if _require_client() else '❌ API key issue')"
   ```

## ✅ Final Checklist

- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Admin user created
- [ ] Database files created and accessible
- [ ] Health endpoint responding
- [ ] JWT authentication working
- [ ] AI assistant endpoints functional
- [ ] CORS properly configured
- [ ] File permissions secured
- [ ] Backup strategy in place

## 🎉 Ready for Production!

Your backend is now ready for deployment. All databases will be created automatically on first startup, and the questionnaire system will work correctly with the database-first approach.