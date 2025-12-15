
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def verify_schema():
    print("Verifying schema...")
    async with engine.connect() as conn:
        # Check tables existence
        tables = [
            "users", "profiles", "pandit_profiles", "wallets", "rates",
            "followers", "messages", "voice_calls", "ratings",
            "languages", "astro_types", "experiences", "kundalis"
        ]
        
        for table in tables:
            result = await conn.execute(text(f"SELECT to_regclass('public.{table}')"))
            if not result.scalar():
                print(f"❌ Table {table} NOT FOUND")
            else:
                print(f"✅ Table {table} exists")

        # Check UUIDs for Users table
        result = await conn.execute(text(
            "SELECT data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'id'"
        ))
        dtype = result.scalar()
        if dtype == 'uuid':
            print("✅ Users.id is UUID")
        else:
            print(f"❌ Users.id is {dtype} (Expected UUID)")

        # Check UUIDs for other tables (sample)
        tables_to_check = ["profiles", "kundalis", "messages"]
        for table in tables_to_check:
            result = await conn.execute(text(
                f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'id'"
            ))
            dtype = result.scalar()
            if dtype == 'uuid':
                 print(f"✅ {table}.id is UUID")
            else:
                 print(f"❌ {table}.id is {dtype} (Expected UUID)")
            
        # Check snake_case (sample check)
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'mobile_no'"
        ))
        if result.scalar():
            print("✅ Users.mobile_no exists (snake_case verified)")
        else:
             print("❌ Users.mobile_no NOT FOUND")

if __name__ == "__main__":
    asyncio.run(verify_schema())
