# 🚀 Nocturnal Archive - Quick Reference

## One-Line Commands

### Setup
\`\`\`bash
./manage.py setup dev --type dev && ./manage.py setup env
\`\`\`

### Development
\`\`\`bash
./manage.py server start --reload
\`\`\`

### Testing
\`\`\`bash
./manage.py test api --coverage
\`\`\`

### Cleanup
\`\`\`bash
./manage.py cleanup
\`\`\`

### Status Check
\`\`\`bash
./manage.py status
\`\`\`

---

## Installation Tiers

| Tier | Command | Size | Use Case |
|------|---------|------|----------|
| Minimal | \`./manage.py setup dev\` | 1.3GB | Production, basic dev |
| Dev | \`./manage.py setup dev --type dev\` | 1.6GB | Development + testing |
| Full | \`./manage.py setup dev --type full\` | 7.8GB | ML features (FinGPT) |

---

## Help
\`\`\`bash
./manage.py --help                # All commands
./manage.py server start --help   # Specific command
\`\`\`

---

See **OPTIMIZED_SETUP.md** for full documentation.
