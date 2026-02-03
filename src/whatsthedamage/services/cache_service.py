"""Cache Service for caching processing results.

This service wraps Flask-Caching with SimpleCache backend for in-memory caching.
Provides abstract protocol for cache implementations.
"""
from typing import Optional, Protocol, runtime_checkable
from whatsthedamage.models.dt_models import CachedProcessingResult


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations.
    
    This allows swapping cache backends (Flask-Caching, Redis, etc.)
    without changing dependent code.
    """
    
    def set(self, key: str, value: CachedProcessingResult, timeout: int) -> None:
        """Store value in cache with timeout."""
        ...
    
    def get(self, key: str) -> Optional[CachedProcessingResult]:
        """Retrieve value from cache."""
        ...
    
    def delete(self, key: str) -> None:
        """Remove value from cache."""
        ...


class CacheService:
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

    def set(self, key: str, value: CachedProcessingResult) -> None:
        """Cache the result."""
        self._cache.set(key, value, timeout=self._ttl)

    def get(self, key: str) -> Optional[CachedProcessingResult]:
        """Retrieve cached result."""
        return self._cache.get(key)

    def delete(self, key: str) -> None:
        """Delete cached result."""
        self._cache.delete(key)
