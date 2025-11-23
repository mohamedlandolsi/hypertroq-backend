"""Create test database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def create_test_db():
    """Create test database."""
    engine = create_async_engine(
        'postgresql+asyncpg://postgres:postgres@localhost:5433/postgres',
        isolation_level="AUTOCOMMIT"
    )
    
    async with engine.connect() as conn:
        # Drop if exists
        try:
            await conn.execute(text('DROP DATABASE IF EXISTS hypertroq_test'))
            print("✅ Dropped existing test database")
        except Exception as e:
            print(f"⚠️  Could not drop database: {e}")
        
        # Create database
        try:
            await conn.execute(text('CREATE DATABASE hypertroq_test'))
            print("✅ Created test database: hypertroq_test")
        except Exception as e:
            print(f"❌ Error creating database: {e}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_db())
