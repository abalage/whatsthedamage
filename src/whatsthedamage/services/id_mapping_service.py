"""ID Mapping Service for secure URL generation.

This service provides bidirectional mapping between sensitive data (account numbers,
category names, timestamps) and opaque identifiers to prevent information leakage
in URLs while maintaining the ability to look up the original data.
"""
from typing import Dict, Optional, Any, cast
import hashlib
from flask_caching import Cache
from whatsthedamage.services.interfaces import IIdMappingService

class IdMappingService(IIdMappingService):
    """Service for mapping sensitive data to opaque identifiers and vice versa."""

    def __init__(self, flask_cache: Cache):
        """Initialize the ID mapping service with Flask-Caching.

        Args:
            flask_cache: Flask-Caching instance for storing ID mappings
        """
        self._cache = flask_cache

    def _generate_deterministic_id(self, prefix: str, value: str) -> str:
        """Generate a deterministic opaque ID from a value.

        Uses SHA-256 hashing to create consistent IDs for the same input.

        Args:
            prefix: ID prefix (e.g., 'acc', 'cat', 'month')
            value: Original value to hash

        Returns:
            Opaque identifier string
        """
        hash_obj = hashlib.sha256(value.encode('utf-8'))
        return f"{prefix}_{hash_obj.hexdigest()[:8]}"

    def get_account_id(self, result_id: str, account_number: str) -> str:
        """Map account number to opaque ID.

        Args:
            result_id: Processing result ID for namespace isolation
            account_number: Original account number

        Returns:
            Opaque account ID
        """
        cache_key = f"mapping:{result_id}:account:{account_number}"
        cached_id = self._cache.get(cache_key)
        if cached_id:
            return cast(str, cached_id)

        # Generate deterministic ID and cache it
        account_id = self._generate_deterministic_id("acc", account_number)
        self._cache.set(cache_key, account_id)

        # Store reverse mapping for lookup
        reverse_cache_key = f"reverse_mapping:{result_id}:account:{account_id}"
        self._cache.set(reverse_cache_key, account_number)
        return account_id

    def get_account_number(self, result_id: str, account_id: str) -> Optional[str]:
        """Reverse mapping: Get original account number from opaque ID.

        Args:
            result_id: Processing result ID for namespace isolation
            account_id: Opaque account ID

        Returns:
            Original account number or None if not found
        """
        reverse_cache_key = f"reverse_mapping:{result_id}:account:{account_id}"
        cached_value = self._cache.get(reverse_cache_key)
        return cast(Optional[str], cached_value)

    def get_category_id(self, result_id: str, category_name: str) -> str:
        """Map category name to opaque ID.

        Args:
            result_id: Processing result ID for namespace isolation
            category_name: Original category name

        Returns:
            Opaque category ID
        """
        cache_key = f"mapping:{result_id}:category:{category_name}"
        cached_id = self._cache.get(cache_key)
        if cached_id:
            return cast(str, cached_id)

        # Generate deterministic ID and cache it
        category_id = self._generate_deterministic_id("cat", category_name)
        self._cache.set(cache_key, category_id)

        # Store reverse mapping for lookup
        reverse_cache_key = f"reverse_mapping:{result_id}:category:{category_id}"
        self._cache.set(reverse_cache_key, category_name)
        return category_id

    def get_category_name(self, result_id: str, category_id: str) -> Optional[str]:
        """Reverse mapping: Get original category name from opaque ID.

        Args:
            result_id: Processing result ID for namespace isolation
            category_id: Opaque category ID

        Returns:
            Original category name or None if not found
        """
        reverse_cache_key = f"reverse_mapping:{result_id}:category:{category_id}"
        cached_value = self._cache.get(reverse_cache_key)
        return cast(Optional[str], cached_value)

    def get_month_id(self, month_timestamp: str) -> str:
        """Map timestamp to opaque month ID using hashing.

        Uses the same approach as accounts and categories for consistent security.

        Args:
            month_timestamp: Unix timestamp string

        Returns:
            Opaque month ID (e.g., 'month_a1b2c3d4')
        """
        cache_key = f"mapping:month:{month_timestamp}"
        cached_id = self._cache.get(cache_key)
        if cached_id:
            return cast(str, cached_id)

        # Generate deterministic ID and cache it
        month_id = self._generate_deterministic_id("month", month_timestamp)
        self._cache.set(cache_key, month_id)

        # Store reverse mapping for lookup
        reverse_cache_key = f"reverse_mapping:month:{month_id}"
        self._cache.set(reverse_cache_key, month_timestamp)
        return month_id

    def get_month_timestamp(self, month_id: str) -> Optional[str]:
        """Reverse mapping: Get original timestamp from opaque month ID.

        Args:
            month_id: Opaque month ID (e.g., 'month_a1b2c3d4')

        Returns:
            Original timestamp string or None if not found
        """
        if not month_id.startswith('month_'):
            return None

        # Look up the original timestamp from cache using reverse mapping
        reverse_cache_key = f"reverse_mapping:month:{month_id}"
        cached_value = self._cache.get(reverse_cache_key)
        return cast(Optional[str], cached_value)

    def create_mappings_for_result(self, result_id: str, dt_responses_by_account: Dict[str, Any]) -> None:
        """Create all necessary mappings for a processing result.

        This method should be called after processing to pre-generate all ID mappings.

        Args:
            result_id: Processing result ID
            dt_responses_by_account: Dictionary of DataTablesResponse by account
        """
        for account_number, dt_response in dt_responses_by_account.items():
            # Create account mapping
            self.get_account_id(result_id, account_number)

            # Create category and month mappings
            for row in dt_response.data:
                self.get_category_id(result_id, row.category)
                self.get_month_id(str(row.date.timestamp))

    def clear_mappings_for_result(self, result_id: str) -> None:
        """Clear all mappings for a specific result.

        Args:
            result_id: Processing result ID to clear
        """
        # Note: Flask-Caching SimpleCache doesn't provide easy key enumeration
        # In production, consider using a more sophisticated cache backend
        # For now, we'll rely on cache timeout for automatic cleanup
        pass