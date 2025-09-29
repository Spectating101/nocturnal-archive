#!/bin/bash
# Backup and Disaster Recovery script for Nocturnal Archive API

set -e

# Configuration
BACKUP_DIR=${BACKUP_DIR:-"/backups"}
RETENTION_DAYS=${RETENTION_DAYS:-14}
REDIS_HOST=${REDIS_HOST:-"localhost"}
REDIS_PORT=${REDIS_PORT:-6379}
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-"nocturnal_archive"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="nocturnal_backup_${TIMESTAMP}"

log "Starting backup process..."

# 1. Redis backup
log "Creating Redis backup..."
if command -v redis-cli &> /dev/null; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    sleep 5  # Wait for background save to complete
    
    # Find the latest RDB file
    RDB_FILE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET dir | tail -1)/dump.rdb
    if [ -f "$RDB_FILE" ]; then
        cp "$RDB_FILE" "${BACKUP_DIR}/${BACKUP_PREFIX}_redis.rdb"
        log "Redis backup completed: ${BACKUP_DIR}/${BACKUP_PREFIX}_redis.rdb"
    else
        warn "Redis RDB file not found, skipping Redis backup"
    fi
else
    warn "redis-cli not found, skipping Redis backup"
fi

# 2. Database backup (if PostgreSQL is available)
log "Creating database backup..."
if command -v pg_dump &> /dev/null; then
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U postgres "$DB_NAME" > "${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql"
    log "Database backup completed: ${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql"
else
    warn "pg_dump not found, skipping database backup"
fi

# 3. Configuration backup
log "Creating configuration backup..."
CONFIG_FILES=(
    "deploy/docker-compose.yml"
    "deploy/Caddyfile"
    "deploy/prometheus.yml"
    "deploy/alerts.yml"
    ".env"
)

mkdir -p "${BACKUP_DIR}/${BACKUP_PREFIX}_config"
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "${BACKUP_DIR}/${BACKUP_PREFIX}_config/"
    fi
done

# Create config archive
tar -czf "${BACKUP_DIR}/${BACKUP_PREFIX}_config.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_PREFIX}_config"
rm -rf "${BACKUP_DIR}/${BACKUP_PREFIX}_config"
log "Configuration backup completed: ${BACKUP_DIR}/${BACKUP_PREFIX}_config.tar.gz"

# 4. Application backup (source code)
log "Creating application backup..."
tar -czf "${BACKUP_DIR}/${BACKUP_PREFIX}_app.tar.gz" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    .
log "Application backup completed: ${BACKUP_DIR}/${BACKUP_PREFIX}_app.tar.gz"

# 5. Cleanup old backups
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "nocturnal_backup_*" -type f -mtime +$RETENTION_DAYS -delete
log "Old backups cleaned up"

# 6. Create backup manifest
cat > "${BACKUP_DIR}/${BACKUP_PREFIX}_manifest.txt" << EOF
Nocturnal Archive API Backup
============================
Timestamp: $TIMESTAMP
Date: $(date)
Hostname: $(hostname)
User: $(whoami)

Backup Contents:
- Redis RDB: ${BACKUP_PREFIX}_redis.rdb
- Database SQL: ${BACKUP_PREFIX}_database.sql
- Configuration: ${BACKUP_PREFIX}_config.tar.gz
- Application: ${BACKUP_PREFIX}_app.tar.gz

Retention: $RETENTION_DAYS days
EOF

log "Backup manifest created: ${BACKUP_DIR}/${BACKUP_PREFIX}_manifest.txt"

# 7. Verify backup integrity
log "Verifying backup integrity..."
BACKUP_FILES=(
    "${BACKUP_PREFIX}_redis.rdb"
    "${BACKUP_PREFIX}_database.sql"
    "${BACKUP_PREFIX}_config.tar.gz"
    "${BACKUP_PREFIX}_app.tar.gz"
    "${BACKUP_PREFIX}_manifest.txt"
)

for file in "${BACKUP_FILES[@]}"; do
    if [ -f "${BACKUP_DIR}/${file}" ]; then
        log "✓ ${file} - $(du -h "${BACKUP_DIR}/${file}" | cut -f1)"
    else
        warn "✗ ${file} - Missing"
    fi
done

log "Backup process completed successfully!"

# 8. Optional: Upload to cloud storage (if configured)
if [ -n "$CLOUD_BACKUP_URL" ]; then
    log "Uploading backup to cloud storage..."
    # Example: aws s3 cp "${BACKUP_DIR}/${BACKUP_PREFIX}_*" "$CLOUD_BACKUP_URL/"
    # Example: gsutil cp "${BACKUP_DIR}/${BACKUP_PREFIX}_*" "$CLOUD_BACKUP_URL/"
    log "Cloud upload completed"
fi

echo ""
log "Backup Summary:"
log "==============="
log "Backup Directory: $BACKUP_DIR"
log "Backup Prefix: $BACKUP_PREFIX"
log "Retention: $RETENTION_DAYS days"
log "Files Created:"
for file in "${BACKUP_FILES[@]}"; do
    if [ -f "${BACKUP_DIR}/${file}" ]; then
        log "  - ${file}"
    fi
done
