#!/usr/bin/env bash

# Simple monitoring script for R/SQL Assistant Server
# Usage: ./monitor.sh [server_url]

SERVER_URL=${1:-"http://localhost:8000"}

echo "=== R/SQL Assistant Server Monitor ==="
echo "Server: $SERVER_URL"
echo "Time: $(date)"
echo ""

# Check if server is responding
if ! curl -s "$SERVER_URL/" > /dev/null; then
    echo "❌ Server is not responding!"
    echo "💡 Check if server is running: sudo systemctl status r-sql-assistant"
    exit 1
fi

echo "✅ Server is responding"
echo ""

# Get server status
echo "📊 Server Status:"
STATUS=$(curl -s "$SERVER_URL/status")
echo "$STATUS" | jq -r '.server_status // "unknown"'
echo ""

# API Key Status
echo "🔑 API Key Status:"
echo "$STATUS" | jq -r '.api_keys[] | "\(.key_id): \(if .is_healthy then "✅" else "❌" end) - \(.requests_today)/\(.daily_limit) requests today"'
echo ""

# Usage Statistics
echo "📈 Usage Statistics:"
STATS=$(curl -s "$SERVER_URL/stats")
echo "$STATS" | jq -r '.request_stats | to_entries[] | "\(.key): \(.value) requests"'
echo ""

# Active Users
USER_COUNT=$(echo "$STATS" | jq -r '.user_stats | length')
echo "👥 Active Users: $USER_COUNT"
echo ""

# System Resources (if available)
if command -v htop >/dev/null 2>&1; then
    echo "💻 System Resources:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo ""
fi

# Recent logs (last 10 lines)
echo "📝 Recent Server Logs:"
sudo journalctl -u r-sql-assistant --since "5 minutes ago" --no-pager | tail -5
echo ""

echo "🔄 Run this script every few minutes to monitor server health"
echo "💡 For continuous monitoring: watch -n 30 ./monitor.sh"
