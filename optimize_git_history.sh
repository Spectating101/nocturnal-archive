#!/bin/bash
# Git History Optimization Script
# Reduces .git size from 566MB by removing large historical files

set -e

echo "🔧 Git History Optimization"
echo "============================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check git status
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Calculate size before
GIT_SIZE_BEFORE=$(du -sh .git | cut -f1)
echo -e "${YELLOW}Current .git size: $GIT_SIZE_BEFORE${NC}"
echo ""

# Warning
echo -e "${YELLOW}⚠️  WARNING: This will rewrite git history!${NC}"
echo ""
echo "This is IRREVERSIBLE and will:"
echo "  • Remove large files from all commits"
echo "  • Change all commit hashes after the removal"
echo "  • Require force push if already pushed to remote"
echo ""
echo "Common large files to remove:"
echo "  • Old .venv directories"
echo "  • Large data files (*.parquet, *.json > 10MB)"
echo "  • Test coverage reports"
echo "  • ML model weights"
echo ""

read -p "Do you want to continue? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Optimization cancelled."
    exit 0
fi

echo ""
echo "📊 Finding large files in git history..."
echo ""

# Find large files in history
git rev-list --objects --all |
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' |
  sed -n 's/^blob //p' |
  sort --numeric-sort --key=2 |
  tail -20 |
  cut -c 1-12,41- |
  $(command -v gnumfmt || echo numfmt) --field=2 --to=iec-i --suffix=B --padding=7 --round=nearest

echo ""
read -p "Proceed with removing large files? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Optimization cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing large files from history..."

# Install git-filter-repo if not available
if ! command -v git-filter-repo &> /dev/null; then
    echo "Installing git-filter-repo..."
    pip install git-filter-repo
fi

# Create backup branch
BACKUP_BRANCH="backup-before-history-cleanup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✓ Created backup branch: $BACKUP_BRANCH${NC}"

# Remove common large files/directories from history
echo "Filtering repository history..."

# Build filter arguments
FILTER_ARGS=""

# Remove .venv directories
FILTER_ARGS="$FILTER_ARGS --path .venv --path nocturnal-archive-api/.venv"

# Remove coverage files
FILTER_ARGS="$FILTER_ARGS --path htmlcov --path .coverage --path nocturnal-archive-api/htmlcov"

# Remove large data files (keep structure, remove large files)
FILTER_ARGS="$FILTER_ARGS --path-glob 'data/sec/sec-edgar-filings/**'"

# Remove test artifacts
FILTER_ARGS="$FILTER_ARGS --path .pytest_cache --path stress_test_results.json"

# Remove Python cache
FILTER_ARGS="$FILTER_ARGS --path-glob '**/__pycache__/**' --path-glob '**/*.pyc'"

# Execute filter
git filter-repo $FILTER_ARGS --force --invert-paths

echo -e "${GREEN}✓ History filtered${NC}"

echo ""
echo "🗜️  Optimizing git repository..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo -e "${GREEN}✓ Repository optimized${NC}"

# Calculate size after
GIT_SIZE_AFTER=$(du -sh .git | cut -f1)

echo ""
echo "✅ Git history optimization complete!"
echo ""
echo -e "${YELLOW}Before: $GIT_SIZE_BEFORE${NC}"
echo -e "${GREEN}After:  $GIT_SIZE_AFTER${NC}"
echo ""
echo "📝 Important notes:"
echo "   • Backup branch created: $BACKUP_BRANCH"
echo "   • All commit hashes have changed"
echo "   • You'll need to force push: git push origin --force --all"
echo "   • Team members will need to re-clone the repository"
echo ""
echo "⚠️  If something went wrong, restore from backup:"
echo "   git checkout $BACKUP_BRANCH"
echo "   git branch -D main"
echo "   git checkout -b main"
