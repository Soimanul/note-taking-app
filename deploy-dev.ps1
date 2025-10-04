# Development Deployment Script for Note Taking App (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Starting development deployment..." -ForegroundColor Green

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
# Development deployment with default values

# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-development-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1,web,frontend

# Database Configuration
POSTGRES_DB=noteapp_dev
POSTGRES_USER=noteuser
POSTGRES_PASSWORD=notepass123

# Redis Configuration
REDIS_URL=redis://redis:6379/0
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "Environment file created with default development values." -ForegroundColor Green
} else {
    Write-Host "Environment file already exists" -ForegroundColor Green
}

# Build application images
Write-Host "Building development images..." -ForegroundColor Blue
docker-compose -f docker-compose-dev.yml build --no-cache

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose-dev.yml down

# Start services
Write-Host "Starting development services..." -ForegroundColor Green
docker-compose -f docker-compose-dev.yml up -d

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "Running database migrations..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose-dev.yml exec web python manage.py migrate
    Write-Host "Database migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Database migrations failed. You may need to run them manually." -ForegroundColor Yellow
}

# Create superuser (optional)
$createSuperuser = Read-Host "Do you want to create a Django superuser? (y/n)"
if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
    try {
        docker-compose -f docker-compose-dev.yml exec web python manage.py createsuperuser
        Write-Host "Superuser creation completed" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Superuser creation failed. You can create one manually later." -ForegroundColor Yellow
    }
}

# Show running services
Write-Host "Development deployment complete! Services status:" -ForegroundColor Green
docker-compose -f docker-compose-dev.yml ps

Write-Host ""
Write-Host "Your development environment is now running at:" -ForegroundColor Cyan
Write-Host "   Backend: http://localhost:8000" -ForegroundColor White
Write-Host "   Backend Admin: http://localhost:8000/admin/" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000/api/" -ForegroundColor White
Write-Host "   Frontend: npm start (run manually in frontend/ directory)" -ForegroundColor White
Write-Host ""
Write-Host "Development features enabled:" -ForegroundColor Cyan
Write-Host "   • Hot reloading with volume mounts" -ForegroundColor White
Write-Host "   • Debug mode enabled" -ForegroundColor White
Write-Host "   • Test tools available (pytest, debug-toolbar)" -ForegroundColor White
Write-Host "   • All source code accessible in containers" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose -f docker-compose-dev.yml logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose -f docker-compose-dev.yml down" -ForegroundColor White
Write-Host "   Run tests: docker-compose -f docker-compose-dev.yml exec web pytest" -ForegroundColor White
Write-Host "   Shell access: docker-compose -f docker-compose-dev.yml exec web bash" -ForegroundColor White
Write-Host "   Production mode: .\deploy.ps1" -ForegroundColor White
Write-Host ""