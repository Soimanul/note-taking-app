# Production Deployment Guide

This guide will help you deploy the Note Taking App in production using Docker Compose.

## 🚀 Quick Start Commands

**Production (default):**
```bash
docker-compose up -d          # Start production environment
docker-compose down           # Stop production environment  
docker-compose logs -f        # View logs
```

**Development:**
```bash
docker-compose -f docker-compose-dev.yml up -d    # Start dev environment
```

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 2GB of available RAM
- At least 5GB of free disk space

## Quick Start

### 1. Prepare Environment Variables

Copy the environment template and configure it:

```bash
# Copy template
cp .env.template .env

# Edit with your values
nano .env  # or your preferred editor
```

### 2. Run Deployment Script

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Access Your Application

- **Frontend**: http://localhost
- **Admin Panel**: http://localhost/admin/
- **API**: http://localhost/api/

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Build and Start Services

```bash
# Build images
docker-compose -f docker-compose-prod.yml build

# Start services in background
docker-compose -f docker-compose-prod.yml up -d
```

### 2. Run Database Migrations

```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py migrate
```

### 3. Create Admin User

```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py createsuperuser
```

### 4. Collect Static Files (if needed)

```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py collectstatic --noinput
```

## Architecture Overview

The production setup includes:

- **Frontend**: React app served by Nginx
- **Backend**: Django API with Gunicorn
- **Database**: PostgreSQL with persistent volume
- **Cache/Queue**: Redis for caching and Celery tasks
- **Worker**: Celery worker for background tasks

## Services Configuration

### Frontend (Nginx + React)
- **Port**: 80 (external)
- **Features**: Static file serving, API proxying, gzip compression
- **Health Check**: HTTP GET /

### Backend (Django + Gunicorn)
- **Port**: 8000 (internal)
- **Workers**: 3 Gunicorn workers
- **Timeout**: 120 seconds
- **Health Check**: HTTP GET /api/health/

### Database (PostgreSQL)
- **Port**: 5432 (internal)
- **Persistent Storage**: Named volume `postgres_data`
- **Health Check**: pg_isready

### Redis
- **Port**: 6379 (internal)
- **Persistent Storage**: Named volume `redis_data`
- **Health Check**: Redis PING

### Celery Worker
- **Concurrency**: 2 workers
- **Queue**: Redis-backed

## Environment Variables

### Required Variables

```env
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
POSTGRES_DB=noteapp_prod
POSTGRES_USER=noteapp_user
POSTGRES_PASSWORD=your-strong-password

# Redis
REDIS_URL=redis://redis:6379/0
```

### Optional Variables

```env
# AI Services (for AI features)
GOOGLE_API_KEY=your-google-ai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-pinecone-env
```

## Security Considerations

### 1. Change Default Values

- Generate a strong `SECRET_KEY`
- Use strong database passwords
- Set proper `ALLOWED_HOSTS`

### 2. Enable HTTPS (Recommended)

Add SSL certificates and update Nginx configuration:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of configuration
}
```

### 3. Environment Security

- Keep `.env` file secure
- Use Docker secrets for sensitive data
- Regularly update base images

## Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose-prod.yml logs -f

# Specific service
docker-compose -f docker-compose-prod.yml logs -f web
```

### Monitor Resource Usage

```bash
# Container stats
docker stats

# Service status
docker-compose -f docker-compose-prod.yml ps
```

### Backup Database

```bash
# Create backup
docker-compose -f docker-compose-prod.yml exec db pg_dump -U noteapp_user noteapp_prod > backup.sql

# Restore backup
docker-compose -f docker-compose-prod.yml exec -i db psql -U noteapp_user noteapp_prod < backup.sql
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose-prod.yml build --no-cache
docker-compose -f docker-compose-prod.yml up -d

# Run migrations if needed
docker-compose -f docker-compose-prod.yml exec web python manage.py migrate
```

## Scaling

### Scale Celery Workers

```bash
docker-compose -f docker-compose-prod.yml up -d --scale worker=3
```

### Scale Web Services

```bash
docker-compose -f docker-compose-prod.yml up -d --scale web=2
```

## Troubleshooting

### Service Won't Start

1. Check logs: `docker-compose -f docker-compose-prod.yml logs [service-name]`
2. Verify environment variables in `.env`
3. Ensure ports are not in use: `netstat -tulpn | grep :80`

### Database Connection Issues

1. Verify database credentials in `.env`
2. Check database service health: `docker-compose -f docker-compose-prod.yml ps`
3. Check database logs: `docker-compose -f docker-compose-prod.yml logs db`

### Frontend Not Loading

1. Check Nginx logs: `docker-compose -f docker-compose-prod.yml logs frontend`
2. Verify API proxy configuration in `frontend/nginx.conf`
3. Check if backend is responding: `curl http://localhost/api/health/`

### Performance Issues

1. Monitor resource usage: `docker stats`
2. Increase worker processes in `docker-compose-prod.yml`
3. Add database indexes if needed
4. Enable database query logging temporarily

## Production Checklist

- [ ] Environment variables configured
- [ ] Strong passwords set
- [ ] `DEBUG=False` in production
- [ ] SSL certificates configured (if using HTTPS)
- [ ] Database backups scheduled
- [ ] Log rotation configured
- [ ] Resource limits set
- [ ] Security headers enabled
- [ ] Firewall configured

## Support

For issues and questions:
1. Check the logs first
2. Review this documentation
3. Check Django and React documentation
4. Create an issue in the project repository