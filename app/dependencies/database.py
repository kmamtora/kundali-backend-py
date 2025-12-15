"""
Database session dependencies for FastAPI.

This module provides dependency injection functions for database
sessions, handling session lifecycle and cleanup.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    This dependency creates a new database session for each request,
    handles automatic commit on success, rollback on error, and
    ensures proper cleanup of the session.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        ```python
        from fastapi import Depends
        from app.dependencies.database import get_db
        
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            user_repo = UserRepository(db)
            users = await user_repo.get_multi()
            return users
        ```
        
    Note:
        - Session is automatically committed if no exceptions occur
        - Session is automatically rolled back if an exception occurs
        - Session is always closed in the finally block
        - This follows the FastAPI dependency injection pattern
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
