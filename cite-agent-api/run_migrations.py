#!/usr/bin/env python3
"""
Database migration runner for Nocturnal Archive
Run this to set up or update the database schema
"""

import asyncio
import asyncpg
import os
from pathlib import Path
import sys

async def run_migrations():
    """Run all migration files in order"""
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("\nSet it like:")
        print("  export DATABASE_URL='postgresql://user:password@localhost/nocturnal_archive'")
        sys.exit(1)
    
    # Connect to database
    print(f"📡 Connecting to database...")
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Get migrations directory
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            print(f"❌ Migrations directory not found: {migrations_dir}")
            sys.exit(1)
        
        # Get all migration files
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            print("⚠️  No migration files found")
            return
        
        print(f"\n📋 Found {len(migration_files)} migration file(s)")
        
        # Run each migration
        for migration_file in migration_files:
            print(f"\n🔨 Running: {migration_file.name}")
            
            # Read migration SQL
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute migration
            try:
                await conn.execute(sql)
                print(f"   ✅ Success!")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                raise
        
        print("\n" + "="*60)
        print("✅ All migrations completed successfully!")
        print("="*60)
        
        # Show some stats
        print("\n📊 Database Statistics:")
        
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"   Tables created: {len(tables)}")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"     - {table['table_name']}: {count} rows")
        
    finally:
        await conn.close()
        print("\n👋 Database connection closed")

def main():
    """Main entry point"""
    print("="*60)
    print("🌙 Nocturnal Archive - Database Migration")
    print("="*60)
    
    try:
        asyncio.run(run_migrations())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

