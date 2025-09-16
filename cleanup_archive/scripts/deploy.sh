#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is required"
    exit 1
fi

# Build and deploy services
echo "Building and deploying Nocturnal Archive..."

# Build Docker images
echo "Building Docker images..."
docker-compose -f deploy/docker/docker-compose.yml build

# Start services
echo "Starting services..."
docker-compose -f deploy/docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."
docker-compose -f deploy/docker/docker-compose.yml ps

echo "Deployment complete! Services are running."