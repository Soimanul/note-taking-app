# Production Django Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (production only)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code selectively (exclude tests and dev files)
COPY config/ ./config/
COPY core/ ./core/
COPY manage.py .

# Remove test files from production image
RUN find . -name "test_*.py" -delete && \
    find . -name "*_test.py" -delete && \
    find . -name "tests.py" -delete

# Create media, static, and cache directories with proper permissions
RUN mkdir -p /app/media/uploads /app/staticfiles /home/appuser/.cache && \
    chown -R appuser:appgroup /app /home/appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh && \
    chown appuser:appgroup /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Set the entrypoint to run migrations before starting Gunicorn
ENTRYPOINT ["/app/docker-entrypoint.sh"]