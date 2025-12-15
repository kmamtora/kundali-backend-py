"""
Database configuration and session management.

This module provides SQLAlchemy 2.0 async engine configuration,
session management, and database connection utilities.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool

from app.core.settings import settings


# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using them
    future=True,
    poolclass=NullPool if settings.is_test else None,  # Use default AsyncAdaptedQueuePool for async
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
        ```
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection.
    
    This function can be called during application startup
    to verify database connectivity.
    """
    async with engine.begin() as conn:
        # Test connection
        await conn.run_sync(lambda _: None)


async def close_db() -> None:
    """
    Close database connections.
    
    This function should be called during application shutdown
    to properly dispose of the connection pool.
    """
    await engine.dispose()
