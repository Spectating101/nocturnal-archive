#!/usr/bin/env python3
"""
Setup PGVector database for FinSight RAG
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def main():
    print("🚀 Setting up PGVector for FinSight RAG")
    print("=======================================")
    
    # Check if PostgreSQL is running
    print("📋 Checking PostgreSQL status...")
    result = run_command("sudo systemctl is-active postgresql", "PostgreSQL status check")
    if "inactive" in result or not result:
        print("Starting PostgreSQL...")
        run_command("sudo systemctl start postgresql", "Start PostgreSQL")
    
    # Install PGVector
    print("📋 Installing PGVector extension...")
    run_command("sudo apt-get update -qq", "Update package list")
    run_command("sudo apt-get install -y postgresql-17-pgvector", "Install PGVector")
    
    # Create database and user
    print("📋 Creating database and user...")
    run_command("sudo -u postgres psql -c 'CREATE DATABASE finsight;'", "Create database")
    run_command("sudo -u postgres psql -c \"CREATE USER finsight_user WITH PASSWORD 'finsight_pass';\"", "Create user")
    run_command("sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE finsight TO finsight_user;'", "Grant privileges")
    
    # Initialize schema
    print("📋 Initializing database schema...")
    run_command("sudo -u postgres psql -d finsight -f init_rag_db.sql", "Initialize schema")
    
    # Verify setup
    print("📋 Verifying setup...")
    run_command("sudo -u postgres psql -d finsight -c 'SELECT \\'PGVector ready\\' as status;'", "Verify PGVector")
    run_command("sudo -u postgres psql -d finsight -c 'SELECT COUNT(*) as documents FROM documents;'", "Check documents")
    
    print("")
    print("✅ PGVector setup complete!")
    print("Database URL: postgresql+psycopg2://finsight_user:finsight_pass@localhost:5432/finsight")
    print("")
    print("Next steps:")
    print("1. Set DB_URL environment variable")
    print("2. Test RAG endpoints")
    print("3. Index real SEC filings")

if __name__ == "__main__":
    main()

