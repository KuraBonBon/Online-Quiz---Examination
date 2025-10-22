# 🚀 PRODUCTION DEPLOYMENT GUIDE
## SPIST School Management System

**Last Updated**: October 21, 2025  
**Target Environment**: Linux Server (Ubuntu 22.04 LTS recommended)  
**Deployment Method**: Nginx + Gunicorn + PostgreSQL

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Critical Items (MUST DO)
- [ ] Generate new SECRET_KEY for production
- [ ] Set DEBUG=False in production environment
- [ ] Configure ALLOWED_HOSTS with actual domain
- [ ] Set up PostgreSQL database
- [ ] Configure email service (SMTP)
- [ ] Obtain SSL/TLS certificate
- [ ] Set up domain DNS records
- [ ] Configure firewall rules
- [ ] Set up backup system
- [ ] Configure error monitoring

### ✅ Security Items
- [ ] All environment variables in .env file
- [ ] .env file excluded from git (.gitignore)
- [ ] Strong database passwords
- [ ] SSH key authentication enabled
- [ ] Firewall configured (UFW)
- [ ] Fail2ban installed
- [ ] SSL/TLS certificate active
- [ ] Security headers enabled

---

## 🖥️ SERVER REQUIREMENTS

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 22.04 LTS or similar
- **Network**: Static IP address

### Recommended for Production
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Backup**: Additional storage for backups
- **CDN**: CloudFlare or similar

---

## 📝 STEP-BY-STEP DEPLOYMENT

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git ufw fail2ban

# Create application user
sudo adduser --disabled-password spist
sudo usermod -aG sudo spist
sudo su - spist
```

### Step 2: PostgreSQL Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE spist_db;
CREATE USER spist_user WITH PASSWORD 'your_strong_password_here';
ALTER ROLE spist_user SET client_encoding TO 'utf8';
ALTER ROLE spist_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE spist_user SET timezone TO 'Asia/Manila';
GRANT ALL PRIVILEGES ON DATABASE spist_db TO spist_user;
\q
```

### Step 3: Application Deployment

```bash
# Create application directory
sudo mkdir -p /var/www/spist
sudo chown spist:spist /var/www/spist
cd /var/www/spist

# Clone repository (or upload files)
git clone https://github.com/your-repo/spist-system.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production packages
pip install psycopg2-binary gunicorn python-decouple whitenoise
```

### Step 4: Environment Configuration

```bash
# Create .env file
nano .env

# Copy contents from .env.example and fill in:
```

```ini
# Production .env configuration
DJANGO_SECRET_KEY=generate_new_secret_key_here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=spist_db
DB_USER=spist_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=SPIST <noreply@yourdomain.com>

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

TIME_ZONE=Asia/Manila
SITE_URL=https://yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
```

```bash
# Secure the .env file
chmod 600 .env
```

### Step 5: Database Migration

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Use production settings
export DJANGO_SETTINGS_MODULE=spist_school.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create directories
mkdir -p media/avatars/student media/avatars/teacher logs backups
chmod 755 media logs backups
```

### Step 6: Gunicorn Configuration

```bash
# Create Gunicorn configuration
nano /var/www/spist/gunicorn_config.py
```

```python
# gunicorn_config.py
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = "/var/www/spist/logs/gunicorn-access.log"
errorlog = "/var/www/spist/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "spist_gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/www/spist/gunicorn.pid"
user = "spist"
group = "spist"
tmp_upload_dir = None

# SSL (if terminating at Gunicorn instead of Nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### Step 7: Systemd Service Setup

```bash
# Create systemd service file
sudo nano /etc/systemd/system/spist.service
```

```ini
[Unit]
Description=SPIST School Management System
After=network.target postgresql.service

[Service]
Type=notify
User=spist
Group=spist
WorkingDirectory=/var/www/spist
Environment="PATH=/var/www/spist/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=spist_school.settings_production"
ExecStart=/var/www/spist/venv/bin/gunicorn \
    --config /var/www/spist/gunicorn_config.py \
    spist_school.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable spist
sudo systemctl start spist
sudo systemctl status spist
```

### Step 8: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/spist
```

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

# HTTPS - Main application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Application settings
    client_max_body_size 5M;
    charset utf-8;
    
    # Access and error logs
    access_log /var/log/nginx/spist_access.log;
    error_log /var/log/nginx/spist_error.log;
    
    # Static files
    location /static/ {
        alias /var/www/spist/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/spist/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/spist /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl status certbot.timer
```

### Step 10: Firewall Configuration

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### Step 11: Fail2ban Setup

```bash
# Configure Fail2ban for Django
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true
```

```bash
sudo systemctl restart fail2ban
```

---

## 🔄 POST-DEPLOYMENT TASKS

### Verify Installation

```bash
# Check service status
sudo systemctl status spist
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
tail -f /var/www/spist/logs/gunicorn-error.log
tail -f /var/log/nginx/spist_error.log
tail -f /var/www/spist/logs/django.log

# Test application
curl -I https://yourdomain.com
```

### Create Backup Script

```bash
# Create backup script
nano /var/www/spist/scripts/backup.sh
```

```bash
#!/bin/bash
# SPIST Backup Script

BACKUP_DIR="/var/www/spist/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="spist_db"
DB_USER="spist_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /var/www/spist/media/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x /var/www/spist/scripts/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /var/www/spist/scripts/backup.sh >> /var/www/spist/logs/backup.log 2>&1
```

---

## 🔧 MAINTENANCE COMMANDS

```bash
# Restart application
sudo systemctl restart spist

# View logs
sudo journalctl -u spist -f

# Update application
cd /var/www/spist
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart spist

# Clear cache (if using Redis)
redis-cli FLUSHDB

# Database backup
pg_dump -U spist_user spist_db > backup.sql
```

---

## 📊 MONITORING

### Health Check
- **URL**: https://yourdomain.com/health/
- **Expected**: HTTP 200 OK

### Log Monitoring
```bash
# Watch application logs
tail -f /var/www/spist/logs/django.log

# Watch Nginx access
tail -f /var/log/nginx/spist_access.log

# Watch Gunicorn errors
tail -f /var/www/spist/logs/gunicorn-error.log
```

---

## 🆘 TROUBLESHOOTING

### Application won't start
```bash
# Check service status
sudo systemctl status spist

# Check logs
journalctl -u spist -n 50

# Test Gunicorn directly
cd /var/www/spist
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 spist_school.wsgi:application
```

### Database connection errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -U spist_user -d spist_db -h localhost
```

### Static files not loading
```bash
# Collect static files again
python manage.py collectstatic --noinput

# Check Nginx permissions
ls -la /var/www/spist/staticfiles/

# Verify Nginx configuration
sudo nginx -t
```

---

## 📞 SUPPORT

For deployment assistance, contact:
- **Technical Support**: support@spist.edu.ph
- **Documentation**: [Project README](README.md)
- **Issues**: GitHub Issues

---

**Deployment Guide Version**: 1.0  
**Last Updated**: October 21, 2025
