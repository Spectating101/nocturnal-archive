#!/bin/bash
# Key rotation script for production deployment

set -e

# Configuration
API_BASE=${API_BASE:-"http://localhost:8000"}
ADMIN_KEY=${ADMIN_KEY:-"admin-key-change-me"}

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

# Generate new keys
NEW_ADMIN_KEY=$(openssl rand -hex 32)
NEW_DEMO_KEY="demo-$(openssl rand -hex 16)"

log "Starting key rotation process..."

# 1. Create new admin key
log "Creating new admin key..."
ADMIN_RESPONSE=$(curl -s -H "X-Admin-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/admin/keys" \
    -H 'content-type: application/json' \
    -d "{\"owner\":\"admin-rotated\",\"tier\":\"admin\"}" \
    | jq -r '.id' 2>/dev/null || echo "error")

if [[ "$ADMIN_RESPONSE" == noct_* ]]; then
    log "New admin key created: $ADMIN_RESPONSE"
    NEW_ADMIN_KEY="$ADMIN_RESPONSE"
else
    error "Failed to create new admin key: $ADMIN_RESPONSE"
fi

# 2. Create new demo key
log "Creating new demo key..."
DEMO_RESPONSE=$(curl -s -H "X-Admin-Key: $NEW_ADMIN_KEY" -X POST "$API_BASE/v1/admin/keys" \
    -H 'content-type: application/json' \
    -d "{\"owner\":\"demo-user\",\"tier\":\"free\"}" \
    | jq -r '.id' 2>/dev/null || echo "error")

if [[ "$DEMO_RESPONSE" == noct_* ]]; then
    log "New demo key created: $DEMO_RESPONSE"
    NEW_DEMO_KEY="$DEMO_RESPONSE"
else
    error "Failed to create new demo key: $DEMO_RESPONSE"
fi

# 3. Revoke old keys (if they exist)
log "Revoking old keys..."
OLD_KEYS=("demo-key-123" "admin-key-change-me")

for old_key in "${OLD_KEYS[@]}"; do
    log "Revoking old key: $old_key"
    curl -s -H "X-Admin-Key: $NEW_ADMIN_KEY" -X POST "$API_BASE/v1/admin/keys/$old_key/revoke" \
        -H 'content-type: application/json' || warn "Failed to revoke $old_key"
done

# 4. Test new keys
log "Testing new keys..."

# Test admin key
ADMIN_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Admin-Key: $NEW_ADMIN_KEY" "$API_BASE/v1/diag/selftest")
if [ "$ADMIN_TEST" = "200" ]; then
    log "✅ New admin key working"
else
    error "❌ New admin key not working (got $ADMIN_TEST)"
fi

# Test demo key
DEMO_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $NEW_DEMO_KEY" -X POST "$API_BASE/api/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}')
if [ "$DEMO_TEST" = "200" ]; then
    log "✅ New demo key working"
else
    error "❌ New demo key not working (got $DEMO_TEST)"
fi

# 5. Generate environment file
log "Generating new environment file..."
cat > .env.prod << EOF
# Production Environment Variables
# Generated: $(date)

# Admin Key (rotated)
ADMIN_KEY=$NEW_ADMIN_KEY

# API Keys (rotated)
DEMO_API_KEY=$NEW_DEMO_KEY

# OpenAI API Key (set manually)
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
OPENALEX_API_KEY=your-openalex-key-here
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your-sentry-dsn-here
ENVIRONMENT=production
LOG_LEVEL=INFO

# Production-specific
BACKUP_DIR=/backups
RETENTION_DAYS=14
CLOUD_BACKUP_URL=your-cloud-storage-url
EOF

log "Environment file generated: .env.prod"

# 6. Summary
echo ""
log "Key Rotation Summary:"
log "==================="
log "New Admin Key: $NEW_ADMIN_KEY"
log "New Demo Key: $NEW_DEMO_KEY"
log "Environment File: .env.prod"
log ""
warn "IMPORTANT: Update your deployment with the new keys!"
warn "IMPORTANT: Set OPENAI_API_KEY in .env.prod before deploying!"
log ""
log "Key rotation completed successfully!"
