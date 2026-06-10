"""Cache Service for caching processing results.

This service wraps Flask-Caching with SimpleCache backend for in-memory caching.
Provides abstract protocol for cache implementations.
"""
from typing import Optional, Protocol, runtime_checkable
from whatsthedamage.models.domain.dt_models import ProcessingResponse
from whatsthedamage.services.interfaces import ICacheService
from flask_caching import Cache
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


class FlaskCacheAdapter:
    """Adapter to make Flask-Caching work with CacheProtocol.

    This adapter allows CacheService to work with Flask-Caching without
    being tightly coupled to it.
    """

    def __init__(self, flask_cache: Cache):
        self._flask_cache = flask_cache

    def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
        """Store value in Flask cache."""
        self._flask_cache.set(key, value, timeout=timeout)

    def get(self, key: str) -> Optional[ProcessingResponse]:
        """Retrieve value from Flask cache."""
        result: Optional[ProcessingResponse] = self._flask_cache.get(key)
        return result

    def delete(self, key: str) -> None:
        """Remove value from Flask cache."""
        self._flask_cache.delete(key)

@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations.

    This allows swapping cache backends (Flask-Caching, Redis, etc.)
    without changing dependent code.
    """

    def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
        """Store value in cache with timeout."""
        ...
    def get(self, key: str) -> Optional[ProcessingResponse]:
        """Retrieve value from cache."""
        ...
    def delete(self, key: str) -> None:
        """Remove value from cache."""
        ...


class CacheService(ICacheService):
    """Service for caching processing results.

    Wraps a cache backend implementing CacheProtocol.
    This provides framework-agnostic caching that works in web, CLI, and API contexts.
    """

    def __init__(self, cache: CacheProtocol, ttl: int = 600):
        """Initialize cache service.

        :param cache: Cache backend implementing CacheProtocol
        :param ttl: Time to live in seconds (default: 600 = 10 minutes)
        """
        self._cache = cache
        self._ttl = ttl

    def set(self, key: str, value: ProcessingResponse, timeout: Optional[int] = None) -> None:
        """Cache the result."""
        actual_timeout = timeout if timeout is not None else self._ttl
        self._cache.set(key, value, timeout=actual_timeout)

    def get(self, key: str) -> Optional[ProcessingResponse]:
        """Retrieve cached result."""
        result = self._cache.get(key)
        if result is None:
            logger.debug(f"Cache miss for key: {key}")
        return result

    def delete(self, key: str) -> None:
        """Delete cached result."""
        self._cache.delete(key)
