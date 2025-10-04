#!/bin/bash
# Development Deployment Script for Note Taking App

set -e  # Exit on any error

echo "Starting development deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
else
    echo "Docker is installed"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
else
    echo "Docker Compose is installed"
fi

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating environment file..."
    cat > .env << EOF
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
EOF
    echo "Environment file created with default development values."
else
    echo "Environment file already exists"
fi

# Build application images
echo "Building development images..."
docker-compose -f docker-compose-dev.yml build --no-cache

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose-dev.yml down

# Start services
echo "Starting development services..."
docker-compose -f docker-compose-dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run database migrations
echo "Running database migrations..."
if docker-compose -f docker-compose-dev.yml exec web python manage.py migrate; then
    echo "Database migrations completed successfully"
else
    echo "Warning: Database migrations failed. You may need to run them manually."
fi

# Create superuser (optional)
echo "Do you want to create a Django superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    if docker-compose -f docker-compose-dev.yml exec web python manage.py createsuperuser; then
        echo "Superuser creation completed"
    else
        echo "Warning: Superuser creation failed. You can create one manually later."
    fi
fi

# Show running services
echo "Development deployment complete! Services status:"
docker-compose -f docker-compose-dev.yml ps

echo ""
echo "Your development environment is now running at:"
echo "   Backend: http://localhost:8000"
echo "   Backend Admin: http://localhost:8000/admin/"
echo "   Backend API: http://localhost:8000/api/"
echo "   Frontend: npm start (run manually in frontend/ directory)"
echo ""
echo "Development features enabled:"
echo "   • Hot reloading with volume mounts"
echo "   • Debug mode enabled"
echo "   • Test tools available (pytest, debug-toolbar)"
echo "   • All source code accessible in containers"
echo ""
echo "Useful commands:"
echo "   View logs: docker-compose -f docker-compose-dev.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose-dev.yml down"
echo "   Run tests: docker-compose -f docker-compose-dev.yml exec web pytest"
echo "   Shell access: docker-compose -f docker-compose-dev.yml exec web bash"
echo "   Production mode: ./deploy.sh"
echo ""