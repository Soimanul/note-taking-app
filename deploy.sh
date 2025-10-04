#!/bin/bash
# Production Deployment Script for Note Taking App

set -e  # Exit on any error

echo "🚀 Starting production deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.template .env
    echo "⚠️  Please edit .env with your values before continuing!"
    echo "   Then run this script again."
    exit 1
fi

# Pull latest images
echo "📥 Pulling latest base images..."
docker-compose pull

# Build application images
echo "🔨 Building application images..."
docker-compose build --no-cache

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start services
echo "🚀 Starting production services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser (optional)
echo "👤 Do you want to create a Django superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    docker-compose exec web python manage.py createsuperuser
fi

# Show running services
echo "✅ Deployment complete! Services status:"
docker-compose ps

echo ""
echo "🌐 Your application is now running at:"
echo "   Frontend: http://localhost"
echo "   Backend Admin: http://localhost/admin/"
echo "   Backend API: http://localhost/api/"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Development mode: docker-compose -f docker-compose-dev.yml up -d"
echo ""