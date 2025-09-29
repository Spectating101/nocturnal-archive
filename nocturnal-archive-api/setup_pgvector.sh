#!/bin/bash
set -e

echo "🚀 Setting up PGVector for FinSight RAG"
echo "======================================="

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
fi

# Install PGVector if not already installed
if ! dpkg -l | grep -q postgresql-17-pgvector; then
    echo "Installing PGVector extension..."
    sudo apt-get update -qq
    sudo apt-get install -y postgresql-17-pgvector
fi

# Create database and user
echo "Creating database and user..."
sudo -u postgres psql -c "CREATE DATABASE finsight;" 2>/dev/null || echo "Database finsight already exists"
sudo -u postgres psql -c "CREATE USER finsight_user WITH PASSWORD 'finsight_pass';" 2>/dev/null || echo "User finsight_user already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE finsight TO finsight_user;"

# Initialize database schema
echo "Initializing database schema..."
sudo -u postgres psql -d finsight -f init_rag_db.sql

# Verify setup
echo "Verifying setup..."
sudo -u postgres psql -d finsight -c "SELECT 'PGVector ready' as status;"
sudo -u postgres psql -d finsight -c "SELECT COUNT(*) as documents FROM documents;"

echo ""
echo "✅ PGVector setup complete!"
echo "Database URL: postgresql+psycopg2://finsight_user:finsight_pass@localhost:5432/finsight"
echo ""
echo "Next steps:"
echo "1. Set DB_URL environment variable"
echo "2. Test RAG endpoints"
echo "3. Index real SEC filings"

