"""
Repository layer for data access.

This package provides repository pattern implementations for
database operations with type-safe async CRUD operations.
"""

from app.repositories.base import BaseRepository
__all__ = [
    "BaseRepository",
]
