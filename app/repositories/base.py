"""
Generic base repository with async CRUD operations.

This module provides a generic repository pattern implementation
with type-safe async CRUD operations for SQLAlchemy models.
"""

from typing import Generic, TypeVar, Type, Optional, Sequence, Any
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with async CRUD operations.
    
    This class provides common database operations for any SQLAlchemy model.
    It uses generics for type safety and supports async operations.
    
    Attributes:
        model: The SQLAlchemy model class
        
    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(User, db)
        ```
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository with model and database session.
        
        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db
    
    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Primary key value (UUID)
            
        Returns:
            Model instance if found, None otherwise
            
        Example:
            ```python
            user = await user_repo.get(user_id)
            ```
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> Sequence[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column to order by (optional)
            
        Returns:
            Sequence of model instances
            
        Example:
            ```python
            users = await user_repo.get_multi(skip=0, limit=10)
            ```
        """
        query = select(self.model).offset(skip).limit(limit)
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Dictionary of field values
            
        Returns:
            Created model instance
            
        Example:
            ```python
            user = await user_repo.create({
                "email": "user@example.com",
                "hashed_password": "...",
                "full_name": "John Doe"
            })
            ```
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        id: UUID,
        obj_in: dict[str, Any],
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: Primary key value (UUID)
            obj_in: Dictionary of field values to update
            
        Returns:
            Updated model instance if found, None otherwise
            
        Example:
            ```python
            user = await user_repo.update(
                user_id,
                {"full_name": "Jane Doe"}
            )
            ```
        """
        # Filter out None values to only update provided fields
        update_data = {k: v for k, v in obj_in.items() if v is not None}
        
        if not update_data:
            return await self.get(id)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Primary key value (UUID)
            
        Returns:
            True if record was deleted, False if not found
            
        Example:
            ```python
            deleted = await user_repo.delete(user_id)
            ```
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """
        Count total number of records.
        
        Returns:
            Total count of records
            
        Example:
            ```python
            total_users = await user_repo.count()
            ```
        """
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            id: Primary key value (UUID)
            
        Returns:
            True if record exists, False otherwise
            
        Example:
            ```python
            if await user_repo.exists(user_id):
                # User exists
                pass
            ```
        """
        result = await self.db.execute(
            select(func.count())
            .select_from(self.model)
            .where(self.model.id == id)
        )
        return result.scalar_one() > 0
