#!/bin/bash
# Disaster recovery restore drill

set -e

echo "🔄 Running disaster recovery restore drill..."

# Configuration
BACKUP_DIR="./backups"
DB_BACKUP_FILE="postgres_backup_$(date +%Y%m%d).sql"
REDIS_BACKUP_FILE="redis_backup_$(date +%Y%m%d).rdb"
RESTORE_LOG="restore_drill_$(date +%Y%m%d_%H%M%S).log"

# Check if backups exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory $BACKUP_DIR not found"
    exit 1
fi

# Find latest backups
LATEST_DB_BACKUP=$(find "$BACKUP_DIR" -name "postgres_backup_*.sql" -type f | sort -r | head -1)
LATEST_REDIS_BACKUP=$(find "$BACKUP_DIR" -name "redis_backup_*.rdb" -type f | sort -r | head -1)

if [ -z "$LATEST_DB_BACKUP" ]; then
    echo "❌ No database backup found"
    exit 1
fi

if [ -z "$LATEST_REDIS_BACKUP" ]; then
    echo "⚠️  No Redis backup found, continuing with DB only"
fi

echo "📦 Found backups:"
echo "  DB: $LATEST_DB_BACKUP"
echo "  Redis: ${LATEST_REDIS_BACKUP:-'None'}"
echo ""

# Start logging
exec > >(tee -a "$RESTORE_LOG")
exec 2>&1

echo "🔄 Starting restore drill at $(date)"
echo "=================================="

# Stop services
echo "🛑 Stopping services..."
docker compose down

# Remove existing volumes (simulate data loss)
echo "🗑️  Removing existing volumes (simulating data loss)..."
docker volume rm $(docker volume ls -q | grep -E "(postgres|redis)") 2>/dev/null || true

# Start services with fresh volumes
echo "🚀 Starting services with fresh volumes..."
docker compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Restore database
echo "📊 Restoring database from $LATEST_DB_BACKUP..."
if docker exec -i $(docker compose ps -q postgres) psql -U postgres -d postgres < "$LATEST_DB_BACKUP"; then
    echo "✅ Database restored successfully"
else
    echo "❌ Database restore failed"
    exit 1
fi

# Restore Redis (if backup exists)
if [ -n "$LATEST_REDIS_BACKUP" ]; then
    echo "🔄 Restoring Redis from $LATEST_REDIS_BACKUP..."
    
    # Stop Redis
    docker compose stop redis
    
    # Copy backup to Redis data directory
    docker run --rm -v $(pwd)/$LATEST_REDIS_BACKUP:/backup.rdb -v $(docker volume inspect $(docker volume ls -q | grep redis | head -1) --format '{{.Mountpoint}}'):/data alpine sh -c "cp /backup.rdb /data/dump.rdb"
    
    # Start Redis
    docker compose start redis
    
    echo "✅ Redis restored successfully"
else
    echo "⚠️  Skipping Redis restore (no backup)"
fi

# Start all services
echo "🚀 Starting all services..."
docker compose up -d

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 10

# Verify restore
echo "🔍 Verifying restore..."

# Check database
if docker exec $(docker compose ps -q postgres) psql -U postgres -d postgres -c "SELECT COUNT(*) FROM api_keys;" >/dev/null 2>&1; then
    echo "✅ Database verification passed"
else
    echo "❌ Database verification failed"
    exit 1
fi

# Check Redis
if docker exec $(docker compose ps -q redis) redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis verification passed"
else
    echo "❌ Redis verification failed"
    exit 1
fi

# Check API health
if curl -f http://localhost:8000/livez >/dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    exit 1
fi

# Run smoke tests
echo "🧪 Running smoke tests..."
if [ -f "../scripts/production_smoke.sh" ]; then
    if bash ../scripts/production_smoke.sh; then
        echo "✅ Smoke tests passed"
    else
        echo "❌ Smoke tests failed"
        exit 1
    fi
else
    echo "⚠️  Smoke test script not found, skipping..."
fi

echo ""
echo "🎉 Restore drill completed successfully!"
echo "========================================"
echo "Restore log: $RESTORE_LOG"
echo "Database backup: $LATEST_DB_BACKUP"
echo "Redis backup: ${LATEST_REDIS_BACKUP:-'None'}"
echo "Completed at: $(date)"

