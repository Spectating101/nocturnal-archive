#!/bin/bash
# Check for secrets in logs - CI hygiene check

set -e

echo "🔍 Checking logs for secrets..."

# Patterns to check for
SECRET_PATTERNS=(
    "sk-[a-zA-Z0-9]{20,}"
    "Bearer [a-zA-Z0-9]{20,}"
    "X-API-Key: [a-zA-Z0-9]{20,}"
    "X-Admin-Key: [a-zA-Z0-9]{20,}"
    "password.*=.*[a-zA-Z0-9]{8,}"
    "secret.*=.*[a-zA-Z0-9]{8,}"
    "token.*=.*[a-zA-Z0-9]{8,}"
    "key.*=.*[a-zA-Z0-9]{8,}"
)

# Directories to check
LOG_DIRS=(
    "/var/log"
    "./logs"
    "./tmp"
    "/tmp"
)

# Files to check
LOG_FILES=(
    "*.log"
    "*.out"
    "*.err"
    "access.log"
    "error.log"
    "application.log"
)

SECRETS_FOUND=0

for pattern in "${SECRET_PATTERNS[@]}"; do
    echo "Checking pattern: $pattern"
    
    for dir in "${LOG_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            for file_pattern in "${LOG_FILES[@]}"; do
                if find "$dir" -name "$file_pattern" -type f 2>/dev/null | head -1 | grep -q .; then
                    if find "$dir" -name "$file_pattern" -type f -exec grep -l "$pattern" {} \; 2>/dev/null | head -1 | grep -q .; then
                        echo "❌ SECRET FOUND in $dir/$file_pattern matching pattern: $pattern"
                        SECRETS_FOUND=$((SECRETS_FOUND + 1))
                    fi
                fi
            done
        fi
    done
done

# Check recent log entries in memory/processes
if command -v journalctl >/dev/null 2>&1; then
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if journalctl --since "1 hour ago" 2>/dev/null | grep -q "$pattern"; then
            echo "❌ SECRET FOUND in systemd journal matching pattern: $pattern"
            SECRETS_FOUND=$((SECRETS_FOUND + 1))
        fi
    done
fi

# Check environment variables (skip placeholder keys)
if [ -f .env ]; then
    if grep -q "sk-[a-zA-Z0-9]\{20,\}" .env || grep -q "Bearer [a-zA-Z0-9]\{20,\}" .env; then
        echo "❌ SECRET FOUND in .env file"
        SECRETS_FOUND=$((SECRETS_FOUND + 1))
    fi
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo "✅ No secrets found in logs"
    exit 0
else
    echo "❌ Found $SECRETS_FOUND potential secrets in logs"
    echo "Please review and redact sensitive information"
    exit 1
fi
