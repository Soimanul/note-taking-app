# Production Deployment Script for Note Taking App (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Starting production deployment..." -ForegroundColor Green

# Check if Docker and Docker Compose are installed
try {
    docker --version | Out-Null
    Write-Host "Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "Docker Compose is installed" -ForegroundColor Green
} catch {
    Write-Host "Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating environment file..." -ForegroundColor Yellow
    $envContent = @"
# Environment Configuration
# Production deployment with default values

# Django Configuration
DEBUG=False
SECRET_KEY=django-insecure-production-key-change-me-please
ALLOWED_HOSTS=localhost,127.0.0.1,web,frontend

# Database Configuration
POSTGRES_DB=noteapp
POSTGRES_USER=noteuser
POSTGRES_PASSWORD=notepass123

# Redis Configuration
REDIS_URL=redis://redis:6379/0
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "Environment file created with default values." -ForegroundColor Green
} else {
    Write-Host "Environment file already exists" -ForegroundColor Green
}

# Pull latest images
Write-Host "Pulling latest base images..." -ForegroundColor Blue
docker-compose pull

# Build application images
Write-Host "Building application images..." -ForegroundColor Blue
docker-compose build --no-cache

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start services
Write-Host "Starting production services..." -ForegroundColor Green
docker-compose up -d

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "Running database migrations..." -ForegroundColor Blue
try {
    docker-compose exec web python manage.py migrate
    Write-Host "Database migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Database migrations failed. You may need to run them manually." -ForegroundColor Yellow
}

# Create superuser (optional)
$createSuperuser = Read-Host "Do you want to create a Django superuser? (y/n)"
if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
    try {
        docker-compose exec web python manage.py createsuperuser
        Write-Host "Superuser creation completed" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Superuser creation failed. You can create one manually later." -ForegroundColor Yellow
    }
}

# Show running services
Write-Host "Deployment complete! Services status:" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "Your application is now running at:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost" -ForegroundColor White
Write-Host "   Backend Admin: http://localhost/admin/" -ForegroundColor White
Write-Host "   Backend API: http://localhost/api/" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose down" -ForegroundColor White
Write-Host "   Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   Development mode: docker-compose -f docker-compose-dev.yml up -d" -ForegroundColor White
Write-Host ""