#!/bin/bash
# Rollback to previous deployment

set -e

echo "🔄 Rolling back to previous deployment..."

# Configuration
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
PREVIOUS_IMAGE_TAG="previous"

# Check if we're in the right directory
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ $COMPOSE_FILE not found. Are you in the deploy directory?"
    exit 1
fi

# Check if backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory $BACKUP_DIR not found"
    exit 1
fi

# Stop current services
echo "🛑 Stopping current services..."
docker compose down

# Check if previous image exists
if ! docker image inspect "nocturnal-archive-api:$PREVIOUS_IMAGE_TAG" >/dev/null 2>&1; then
    echo "❌ Previous image not found. Cannot rollback."
    echo "Available images:"
    docker images | grep nocturnal-archive-api || echo "No nocturnal-archive-api images found"
    exit 1
fi

# Tag current image as backup
echo "📦 Tagging current image as backup..."
CURRENT_IMAGE=$(docker compose config --services | head -1)
if docker image inspect "$CURRENT_IMAGE:latest" >/dev/null 2>&1; then
    docker tag "$CURRENT_IMAGE:latest" "$CURRENT_IMAGE:backup-$(date +%Y%m%d-%H%M%S)"
fi

# Tag previous image as latest
echo "🔄 Tagging previous image as latest..."
docker tag "nocturnal-archive-api:$PREVIOUS_IMAGE_TAG" "nocturnal-archive-api:latest"

# Start services with previous image
echo "🚀 Starting services with previous image..."
docker compose up -d

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 10

# Check if services are healthy
if curl -f http://localhost:8000/livez >/dev/null 2>&1; then
    echo "✅ Rollback successful! Services are healthy."
    
    # Run smoke tests
    echo "🧪 Running smoke tests..."
    if [ -f "../scripts/production_smoke.sh" ]; then
        bash ../scripts/production_smoke.sh
    else
        echo "⚠️  Smoke test script not found, skipping..."
    fi
    
else
    echo "❌ Rollback failed! Services are not healthy."
    echo "Check logs: docker compose logs"
    exit 1
fi

echo "🎉 Rollback completed successfully!"
echo "Previous image: nocturnal-archive-api:$PREVIOUS_IMAGE_TAG"
echo "Current image: nocturnal-archive-api:latest"

