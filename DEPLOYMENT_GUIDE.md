# Cite-Agent Deployment Guide

## 🚀 Production Deployment

### Prerequisites

- **Python 3.8+**
- **PostgreSQL 12+**
- **Redis** (for caching)
- **Domain name** (optional)
- **SSL certificate** (recommended)

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cite_agent
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=your-secret-key
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cite_agent
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Deploy

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec web python run_migrations.py

# Check logs
docker-compose logs -f web
```

---

## ☁️ Cloud Deployment

### Heroku (Recommended for MVP)

#### 1. Prepare Application

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create app
heroku create cite-agent-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini
```

#### 2. Configure Environment

```bash
# Set environment variables
heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)
heroku config:set NOCTURNAL_DEBUG=0
heroku config:set ENVIRONMENT=production

# Set API keys (get from respective services)
heroku config:set GROQ_API_KEY_1=your_groq_key
heroku config:set OPENALEX_API_KEY=your_openalex_key
heroku config:set SEMANTIC_SCHOLAR_API_KEY=your_semantic_key
```

#### 3. Deploy

```bash
# Deploy to Heroku
git push heroku main

# Run migrations
heroku run python run_migrations.py

# Check logs
heroku logs --tail
```

#### 4. Custom Domain (Optional)

```bash
# Add custom domain
heroku domains:add api.cite-agent.com

# Configure DNS
# Point CNAME to: cite-agent-api-720dfadd602c.herokuapp.com
```

### Railway

#### 1. Connect Repository

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

#### 2. Configure Environment

```bash
# Set variables in Railway dashboard or CLI
railway variables set JWT_SECRET_KEY=your-secret-key
railway variables set DATABASE_URL=postgresql://...
```

### DigitalOcean App Platform

#### 1. Create App

```yaml
# .do/app.yaml
name: cite-agent-api
services:
- name: web
  source_dir: cite-agent-api
  github:
    repo: yourusername/cite-agent
    branch: main
  run_command: uvicorn src.main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: JWT_SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: postgresql://...
databases:
- name: cite-agent-db
  engine: PG
  version: "15"
```

#### 2. Deploy

```bash
# Deploy via GitHub integration
# Or use doctl CLI
doctl apps create --spec .do/app.yaml
```

---

## 🗄️ Database Setup

### PostgreSQL Configuration

#### 1. Create Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE cite_agent;

-- Create user
CREATE USER cite_agent_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE cite_agent TO cite_agent_user;
```

#### 2. Run Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python run_migrations.py

# Verify tables
psql -U cite_agent_user -d cite_agent -c "\dt"
```

#### 3. Production Optimizations

```sql
-- Add indexes for performance
CREATE INDEX CONCURRENTLY idx_queries_user_timestamp ON queries(user_id, timestamp);
CREATE INDEX CONCURRENTLY idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX CONCURRENTLY idx_downloads_platform_timestamp ON downloads(platform, timestamp);

-- Set up connection pooling
-- In postgresql.conf:
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
```

---

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Authentication
JWT_SECRET_KEY=your-32-char-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# API Keys
GROQ_API_KEY_1=your_groq_key
GROQ_API_KEY_2=backup_groq_key
OPENALEX_API_KEY=your_openalex_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_key

# External APIs
ARCHIVE_API_URL=https://your-api.com/api
FINSIGHT_API_URL=https://your-api.com/v1/finance

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_BURST=100

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Monitoring
SENTRY_DSN=your_sentry_dsn
TELEMETRY_ENDPOINT=https://your-telemetry.com/ingest
```

### Optional Environment Variables

```bash
# Custom domains
ALLOWED_HOSTS=api.cite-agent.com,localhost

# CORS
CORS_ORIGINS=https://cite-agent.com,https://app.cite-agent.com

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET=cite-agent-uploads

# Admin
ADMIN_EMAIL=admin@cite-agent.com
ADMIN_PASSWORD=secure_admin_password
```

---

## 📊 Monitoring & Logging

### Application Monitoring

#### 1. Health Checks

```python
# Add to main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.5",
        "database": await check_database(),
        "redis": await check_redis()
    }
```

#### 2. Metrics Collection

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### 3. Error Tracking

```python
# Add Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

### Logging Configuration

```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Use structured logging
logger.info("User registered", extra={
    "user_id": user_id,
    "email": email,
    "timestamp": datetime.now().isoformat()
})
```

---

## 🔒 Security Configuration

### SSL/TLS Setup

#### 1. Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d api.cite-agent.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### 2. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/cite-agent
server {
    listen 80;
    server_name api.cite-agent.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.cite-agent.com;
    
    ssl_certificate /etc/letsencrypt/live/api.cite-agent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.cite-agent.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Headers

```python
# Add security middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["api.cite-agent.com", "localhost"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cite-agent.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "cite-agent-api"
          heroku_email: "your-email@example.com"
```

### Docker Hub

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t cite-agent/api:latest .
      - name: Push to Docker Hub
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push cite-agent/api:latest
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_queries_user_timestamp ON queries(user_id, timestamp DESC);
CREATE INDEX CONCURRENTLY idx_sessions_token ON sessions(token);
CREATE INDEX CONCURRENTLY idx_downloads_platform ON downloads(platform);

-- Partition large tables
CREATE TABLE queries_2024 PARTITION OF queries
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Caching Strategy

```python
# Redis caching
import redis
from functools import wraps

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### Load Balancing

```nginx
# nginx.conf
upstream cite_agent_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://cite_agent_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔄 Backup & Recovery

### Database Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cite_agent_backup_$DATE.sql"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE.gz s3://cite-agent-backups/

# Cleanup old backups (keep 30 days)
find /backups -name "cite_agent_backup_*.sql.gz" -mtime +30 -delete
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

---

## 🎯 Production Checklist

### Pre-Launch

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Error tracking setup
- [ ] Logging configured
- [ ] Backup strategy implemented
- [ ] Security headers added
- [ ] Rate limiting configured
- [ ] Health checks working

### Post-Launch

- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify all endpoints working
- [ ] Test authentication flow
- [ ] Monitor database performance
- [ ] Check log aggregation
- [ ] Verify backup process
- [ ] Test failover procedures

---

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
heroku pg:info --app cite-agent-api
```

#### High Memory Usage
```bash
# Check memory usage
heroku ps --app cite-agent-api

# Scale up if needed
heroku ps:scale web=2 --app cite-agent-api
```

#### Slow Response Times
```bash
# Check database queries
heroku pg:psql --app cite-agent-api -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Add database indexes
heroku pg:psql --app cite-agent-api -c "CREATE INDEX CONCURRENTLY idx_queries_timestamp ON queries(timestamp);"
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Heroku rollback
heroku rollback --app cite-agent-api

# Docker rollback
docker-compose down
docker-compose up -d --scale web=0
docker-compose up -d --scale web=1
```

#### Database Recovery
```bash
# Restore from backup
pg_restore --clean --no-acl --no-owner -d $DATABASE_URL backup.sql
```

---

**Your Cite-Agent API is now production-ready!** 🚀