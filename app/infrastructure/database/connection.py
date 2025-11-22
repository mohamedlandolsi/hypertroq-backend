"""Async database connection and session management."""
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event

from app.core.config import settings
from app.infrastructure.database.base import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self) -> None:
        """Initialize database manager."""
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None
    
    def get_engine(self) -> AsyncEngine:
        """
        Get or create the async database engine.
        
        Returns:
            AsyncEngine instance
        """
        if self._engine is None:
            # Use DIRECT_URL if available (bypasses pgBouncer), otherwise use DATABASE_URL
            # DIRECT_URL connects directly to Postgres, avoiding pgBouncer statement cache issues
            database_url = str(settings.DIRECT_URL) if settings.DIRECT_URL else str(settings.DATABASE_URL)
            
            # Connection pool settings
            pool_class = QueuePool if not settings.DEBUG else NullPool
            
            # Build engine kwargs
            engine_kwargs = {
                "echo": settings.DB_ECHO,
                "pool_pre_ping": True,  # Verify connections before using
                "poolclass": pool_class,
                "connect_args": {
                    "server_settings": {"application_name": settings.APP_NAME},
                    "timeout": 30,  # Connection timeout in seconds
                },
            }
            
            # Only add pool settings if not using NullPool
            if pool_class != NullPool:
                engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
                engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
                engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour
            
            # If using pgBouncer (pooled connection), disable statement caching
            if "pooler" in database_url or "pgbouncer" in database_url.lower():
                engine_kwargs["connect_args"]["statement_cache_size"] = 0
                logger.info("Detected pgBouncer - disabling statement cache")
            
            self._engine = create_async_engine(
                database_url,
                **engine_kwargs
            )
            
            # Add event listeners
            self._add_engine_events()
            
            logger.info("Database engine created successfully")
        
        return self._engine
    
    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create the async session maker.
        
        Returns:
            async_sessionmaker instance
        """
        if self._session_maker is None:
            engine = self.get_engine()
            self._session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autoflush=False,  # Don't auto-flush before queries
                autocommit=False,  # Don't auto-commit
            )
            logger.info("Database session maker created successfully")
        
        return self._session_maker
    
    def _add_engine_events(self) -> None:
        """Add event listeners to the database engine."""
        if self._engine is None:
            return
        
        @event.listens_for(self._engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Event listener for new database connections."""
            logger.debug("New database connection established")
        
        @event.listens_for(self._engine.sync_engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Event listener for closed database connections."""
            logger.debug("Database connection closed")
    
    async def init_db(self) -> None:
        """
        Initialize database by creating all tables.
        
        Note: This should only be used in development.
        In production, use Alembic migrations.
        """
        engine = self.get_engine()
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered
            from app.models import UserModel  # noqa: F401
            
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    
    async def drop_db(self) -> None:
        """
        Drop all database tables.
        
        Warning: This will delete all data!
        Should only be used in testing/development.
        """
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
    
    async def close(self) -> None:
        """Close database connections and dispose of the engine."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions.
        
        Usage:
            async with db_manager.session() as session:
                result = await session.execute(...)
        
        Yields:
            AsyncSession instance
        """
        session_maker = self.get_session_maker()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage in routes:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    Yields:
        AsyncSession instance
    """
    session_maker = db_manager.get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """
    Initialize the database.
    
    This function should be called on application startup.
    It creates the database engine and session maker.
    """
    try:
        # Initialize engine and session maker
        db_manager.get_engine()
        db_manager.get_session_maker()
        
        logger.info("Database initialized successfully")
        
        # Optional: Create tables in development
        if settings.is_development and settings.DEBUG:
            await db_manager.init_db()
            logger.info("Database tables created (development mode)")
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close database connections.
    
    This function should be called on application shutdown.
    """
    try:
        await db_manager.close()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# Backward compatibility with existing code
engine = None  # Will be set via db_manager.get_engine()
async_session_maker = None  # Will be set via db_manager.get_session_maker()


def get_engine() -> AsyncEngine:
    """Get the database engine (backward compatibility)."""
    return db_manager.get_engine()


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get the session maker (backward compatibility)."""
    return db_manager.get_session_maker()
