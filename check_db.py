"""Script to check database tables."""
import asyncio
from sqlalchemy import text
from app.infrastructure.database import get_engine


async def check_tables():
    """Check existing tables in database."""
    engine = get_engine()
    async with engine.connect() as conn:
        # List all tables
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        )
        tables = [row[0] for row in result]
        print("\n🗄️  Existing tables in database:")
        for table in tables:
            print(f"   - {table}")
        
        # Check if users table exists
        if 'users' in tables:
            print("\n✅ 'users' table exists")
            # Get column info
            result = await conn.execute(
                text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'users'
                    ORDER BY ordinal_position
                """)
            )
            print("\n   Columns:")
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"   - {row[0]}: {row[1]} ({nullable})")
        
        # Check for knowledgeItem table
        if 'knowledgeItem' in tables or 'knowledgeitem' in tables:
            print("\n✅ 'knowledgeItem' table exists")
        
        print("\n✅ Database connection successful!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_tables())
