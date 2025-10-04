# Production Deployment Script for Note Taking App (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting production deployment..." -ForegroundColor Green

# Check if Docker and Docker Compose are installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating environment file..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "⚠️  Please edit .env with your values before continuing!" -ForegroundColor Yellow
    Write-Host "   Then run this script again." -ForegroundColor Yellow
    exit 1
}

# Pull latest images
Write-Host "📥 Pulling latest base images..." -ForegroundColor Blue
docker-compose pull

# Build application images
Write-Host "🔨 Building application images..." -ForegroundColor Blue
docker-compose build --no-cache

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start services
Write-Host "🚀 Starting production services..." -ForegroundColor Green
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Blue
docker-compose exec web python manage.py migrate

# Create superuser (optional)
$createSuperuser = Read-Host "👤 Do you want to create a Django superuser? (y/n)"
if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
    docker-compose exec web python manage.py createsuperuser
}

# Show running services
Write-Host "✅ Deployment complete! Services status:" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "🌐 Your application is now running at:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost" -ForegroundColor White
Write-Host "   Backend Admin: http://localhost/admin/" -ForegroundColor White
Write-Host "   Backend API: http://localhost/api/" -ForegroundColor White
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose down" -ForegroundColor White
Write-Host "   Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   Development mode: docker-compose -f docker-compose-dev.yml up -d" -ForegroundColor White
Write-Host ""