#!/bin/bash

# Production Deployment Script for Nocturnal Archive
# This script handles the complete production deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="nocturnal-archive"
ENVIRONMENT="production"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f ".env.production" ]; then
        log_error "Production environment file (.env.production) not found."
        log_info "Please create .env.production based on env.production.example"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database volumes if they exist
    if docker volume ls | grep -q "${PROJECT_NAME}_mongo_data"; then
        log_info "Backing up MongoDB data..."
        docker run --rm -v "${PROJECT_NAME}_mongo_data:/data" -v "$(pwd)/$BACKUP_DIR:/backup" mongo:7.0 tar czf /backup/mongo_backup.tar.gz -C /data .
    fi
    
    if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
        log_info "Backing up PostgreSQL data..."
        docker run --rm -v "${PROJECT_NAME}_postgres_data:/data" -v "$(pwd)/$BACKUP_DIR:/backup" postgres:15-alpine tar czf /backup/postgres_backup.tar.gz -C /data .
    fi
    
    log_success "Backup created in $BACKUP_DIR"
}

# Build and deploy
deploy() {
    log_info "Starting production deployment..."
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.production.yml down --remove-orphans
    
    # Build images
    log_info "Building production images..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Health checks
    log_info "Performing health checks..."
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed"
        exit 1
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend health check failed"
        exit 1
    fi
    
    log_success "Deployment completed successfully!"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create monitoring directories
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    # Setup Grafana datasource
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    log_success "Monitoring setup completed"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    mkdir -p nginx/ssl
    
    # Generate self-signed certificate for development
    # In production, replace with real certificates
    if [ ! -f "nginx/ssl/cert.pem" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Main deployment process
main() {
    log_info "Starting Nocturnal Archive Production Deployment"
    log_info "================================================"
    
    check_prerequisites
    create_backup
    setup_ssl
    setup_monitoring
    deploy
    
    log_success "================================================"
    log_success "Nocturnal Archive is now running in production!"
    log_success "================================================"
    log_info "Services:"
    log_info "  - Frontend: https://localhost"
    log_info "  - Backend API: https://localhost/api"
    log_info "  - Grafana: http://localhost:3001"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Kibana: http://localhost:5601"
    log_info "  - Redis Commander: http://localhost:8081"
    log_info "  - Adminer: http://localhost:8080"
    log_info ""
    log_info "To view logs: docker-compose -f docker-compose.production.yml logs -f"
    log_info "To stop: docker-compose -f docker-compose.production.yml down"
}

# Run main function
main "$@"

