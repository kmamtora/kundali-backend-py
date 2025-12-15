#!/usr/bin/env python3
"""
Database initialization script.

This script creates the initial database schema by running all Alembic migrations.
It should be run after setting up the database server and before starting the application.

Usage:
    python scripts/init_db.py
    
    Or with UV:
    uv run python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.database import engine
from app.core.settings import settings


async def check_database_connection() -> bool:
    """
    Check if database connection is available.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def run_migrations() -> None:
    """
    Run Alembic migrations to create/update database schema.
    """
    try:
        # Load Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations to head
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise


async def verify_schema() -> bool:
    """
    Verify that the database schema was created correctly.
    
    Returns:
        True if schema exists, False otherwise
    """
    try:
        async with engine.begin() as conn:
            # Check if alembic_version table exists
            result = await conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                    """
                )
            )
            table_exists = result.scalar()
            
            if table_exists:
                print("✓ Database schema verified (alembic_version table exists)")
                return True
            else:
                print("✗ Database schema verification failed (alembic_version table not found)")
                return False
    except Exception as e:
        print(f"✗ Schema verification failed: {e}")
        return False


async def main() -> None:
    """
    Main function to initialize the database.
    """
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    print("=" * 60)
    print()
    
    # Step 1: Check database connection
    print("Step 1: Checking database connection...")
    if not await check_database_connection():
        print("\nDatabase initialization failed!")
        print("Please ensure:")
        print("  1. PostgreSQL server is running")
        print("  2. Database credentials are correct in .env file")
        print("  3. Database exists (create it if needed)")
        sys.exit(1)
    print()
    
    # Step 2: Run migrations
    print("Step 2: Running database migrations...")
    try:
        run_migrations()
    except Exception:
        print("\nDatabase initialization failed!")
        sys.exit(1)
    print()
    
    # Step 3: Verify schema
    print("Step 3: Verifying database schema...")
    if not await verify_schema():
        print("\nDatabase initialization completed with warnings!")
        print("Schema verification failed, but migrations ran successfully.")
        sys.exit(1)
    print()
    
    # Cleanup
    await engine.dispose()
    
    print("=" * 60)
    print("✓ Database initialization completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start the application: make dev")
    print()


if __name__ == "__main__":
    asyncio.run(main())
