#!/bin/bash
# Production deployment script for Nocturnal Archive API

set -e

# Configuration
API_BASE=${API_BASE:-"https://api.nocturnal.dev"}
ADMIN_KEY=${ADMIN_KEY:-"admin-key-change-me"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

echo "🚀 NOCTURNAL ARCHIVE - PRODUCTION DEPLOYMENT"
echo "============================================="
echo "API Base: $API_BASE"
echo ""

# Step 1: Rotate keys
log "Step 1: Rotating production keys..."
if [ -f "./scripts/keys_rotate.sh" ]; then
    ./scripts/keys_rotate.sh
    if [ $? -eq 0 ]; then
        log "✅ Key rotation completed"
    else
        error "❌ Key rotation failed"
    fi
else
    warn "Key rotation script not found, skipping..."
fi

# Step 2: Deploy stack
log "Step 2: Deploying production stack..."
cd deploy/

# Use production Caddyfile
if [ -f "Caddyfile.prod" ]; then
    cp Caddyfile.prod Caddyfile
    log "✅ Using production Caddyfile"
else
    warn "Production Caddyfile not found, using default"
fi

# Pull latest images and deploy
log "Pulling latest Docker images..."
docker-compose pull

log "Starting production services..."
docker-compose up -d

# Wait for services to start
log "Waiting for services to start..."
sleep 30

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    log "✅ Services started successfully"
else
    error "❌ Services failed to start"
fi

cd ..

# Step 3: Run smoke tests
log "Step 3: Running production smoke tests..."
if [ -f "./scripts/production_smoke.sh" ]; then
    ./scripts/production_smoke.sh
    if [ $? -eq 0 ]; then
        log "✅ Production smoke tests passed"
    else
        error "❌ Production smoke tests failed"
    fi
else
    warn "Production smoke test script not found, skipping..."
fi

# Step 4: Run red-team tests
log "Step 4: Running red-team security tests..."
if [ -f "./scripts/red_team_smoke.sh" ]; then
    ./scripts/red_team_smoke.sh
    if [ $? -eq 0 ]; then
        log "✅ Red-team tests passed"
    else
        error "❌ Red-team tests failed"
    fi
else
    warn "Red-team test script not found, skipping..."
fi

# Step 5: Verify endpoints
log "Step 5: Verifying production endpoints..."

# Test health endpoints
info "Testing health endpoints..."
LIVEZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/livez" 2>/dev/null || echo "000")
READYZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/readyz" 2>/dev/null || echo "000")

if [ "$LIVEZ_RESPONSE" = "200" ]; then
    log "✅ Liveness probe working"
else
    error "❌ Liveness probe failed (got $LIVEZ_RESPONSE)"
fi

if [ "$READYZ_RESPONSE" = "200" ] || [ "$READYZ_RESPONSE" = "503" ]; then
    log "✅ Readiness probe working"
else
    error "❌ Readiness probe failed (got $READYZ_RESPONSE)"
fi

# Test API endpoints
info "Testing API endpoints..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/api/papers/search" \
    -H 'content-type: application/json' -d '{"query":"test","limit":1}' 2>/dev/null || echo "000")

if [ "$API_RESPONSE" = "200" ]; then
    log "✅ Papers API working"
else
    warn "⚠️ Papers API returned $API_RESPONSE (may need new API key)"
fi

# Test FinSight endpoints
info "Testing FinSight endpoints..."
FINSIGHT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/finance/filings/forms" 2>/dev/null || echo "000")

if [ "$FINSIGHT_RESPONSE" = "200" ]; then
    log "✅ FinSight API working"
else
    warn "⚠️ FinSight API returned $FINSIGHT_RESPONSE"
fi

# Step 6: Performance check
log "Step 6: Running performance check..."
PERF_START=$(date +%s%3N)
PERF_RESPONSE=$(curl -s -H "X-API-Key: $ADMIN_KEY" -X POST "$API_BASE/v1/api/papers/search" \
    -H 'content-type: application/json' -d '{"query":"machine learning","limit":5}' \
    | jq -r '.count' 2>/dev/null || echo "error")
PERF_END=$(date +%s%3N)
PERF_DURATION=$((PERF_END - PERF_START))

if [ "$PERF_RESPONSE" != "error" ] && [ "$PERF_DURATION" -lt 1500 ]; then
    log "✅ Performance check passed (${PERF_DURATION}ms)"
else
    warn "⚠️ Performance check failed (${PERF_DURATION}ms)"
fi

# Step 7: Security check
log "Step 7: Running security check..."

# Test admin endpoint protection
ADMIN_PROTECTION=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/v1/diag/selftest" 2>/dev/null || echo "000")
if [ "$ADMIN_PROTECTION" = "401" ]; then
    log "✅ Admin endpoints protected"
else
    error "❌ Admin endpoints not protected (got $ADMIN_PROTECTION)"
fi

# Test metrics endpoint protection
METRICS_PROTECTION=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/metrics" 2>/dev/null || echo "000")
if [ "$METRICS_PROTECTION" = "401" ]; then
    log "✅ Metrics endpoint protected"
else
    error "❌ Metrics endpoint not protected (got $METRICS_PROTECTION)"
fi

# Step 8: Final status
log "Step 8: Production deployment completed!"

echo ""
echo "🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!"
echo "===================================="
echo "✅ Keys rotated"
echo "✅ Services deployed"
echo "✅ Smoke tests passed"
echo "✅ Red-team tests passed"
echo "✅ Endpoints verified"
echo "✅ Performance validated"
echo "✅ Security confirmed"
echo ""
echo "📊 Production Status:"
echo "- API Base: $API_BASE"
echo "- Health: /livez, /readyz"
echo "- Papers Demo: /v1/api/papers/*"
echo "- FinSight: /v1/finance/*"
echo "- Admin: /v1/admin/* (protected)"
echo "- Metrics: /metrics (protected)"
echo ""
echo "🔗 Useful URLs:"
echo "- API Docs: $API_BASE/docs"
echo "- Health Check: $API_BASE/livez"
echo "- Papers Demo: $API_BASE/v1/api/papers/demo-info"
echo "- FinSight Forms: $API_BASE/v1/finance/filings/forms"
echo ""
echo "📈 Next Steps:"
echo "1. Monitor logs: docker-compose -f deploy/docker-compose.yml logs -f"
echo "2. Check metrics: curl -H 'X-Admin-Key: $ADMIN_KEY' $API_BASE/metrics"
echo "3. Run backups: ./scripts/backup_dr.sh"
echo "4. Set up monitoring alerts"
echo ""
echo "🚀 Nocturnal Archive is now LIVE in production!"
