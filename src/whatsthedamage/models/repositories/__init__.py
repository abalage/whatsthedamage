"""Repositories package.

This package contains the repository implementations for data access layer.
Uses the repository pattern to abstract database operations.
"""

from whatsthedamage.models.repositories.base_repository import BaseRepository
from whatsthedamage.models.repositories.user_repository import (
    UserRepository,
    SqlAlchemyUserRepository
)
from whatsthedamage.models.repositories.session_repository import (
    SessionRepository,
    SqlAlchemySessionRepository
)

__all__ = [
    'BaseRepository',
    'UserRepository',
    'SqlAlchemyUserRepository',
    'SessionRepository',
    'SqlAlchemySessionRepository',
]
