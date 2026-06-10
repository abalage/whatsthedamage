"""Test factory for creating DrilldownResponseService with test doubles.

This module provides utilities for creating DrilldownResponseService instances
with mock dependencies for unit testing.
"""
from typing import Dict, Optional, Any, List
from whatsthedamage.services.drilldown_response_service import DrilldownResponseService
from whatsthedamage.services.interfaces import (
    IIdMappingService, ICacheService,
    IDataFormattingService, IStatisticalAnalysisService
)
from whatsthedamage.models.dt_models import AccountResponse, StatisticalMetadata

class MockIdMappingService(IIdMappingService):
    """Mock implementation of IIdMappingService for testing."""

    def __init__(self, mappings: Optional[Dict] = None):
        """Initialize mock ID mapping service.

        Args:
            mappings: Dictionary containing predefined mappings
        """
        self._mappings = mappings or {}
        self._reverse_mappings = {}

    def get_account_number(self, result_id: str, account_id: str) -> Optional[str]:
        """Get original account number from secure account ID."""
        key = f"account:{result_id}:{account_id}"
        return self._mappings.get(key)

    def get_account_id(self, result_id: str, account_number: str) -> Optional[str]:
        """Get secure account ID from original account number."""
        key = f"account_reverse:{result_id}:{account_number}"
        return self._mappings.get(key)

    def get_category_name(self, result_id: str, category_id: str) -> Optional[str]:
        """Get original category name from secure category ID."""
        key = f"category:{result_id}:{category_id}"
        return self._mappings.get(key)

    def get_category_id(self, result_id: str, category_name: str) -> Optional[str]:
        """Get secure category ID from original category name."""
        key = f"category_reverse:{result_id}:{category_name}"
        return self._mappings.get(key)

    def get_month_timestamp(self, month_id: str) -> Optional[str]:
        """Get original month timestamp from secure month ID."""
        return self._mappings.get(f"month:{month_id}")

    def get_month_id(self, month_timestamp: str) -> Optional[str]:
        """Get secure month ID from original month timestamp."""
        return self._mappings.get(f"month_reverse:{month_timestamp}")

class MockCacheService(ICacheService):
    """Mock implementation of ICacheService for testing."""

    def __init__(self, cache_data: Optional[Dict] = None):
        """Initialize mock cache service.

        Args:
            cache_data: Dictionary containing cached data
        """
        self._cache = cache_data or {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data by key."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Store data in cache."""
        self._cache[key] = value

class MockDataFormattingService(IDataFormattingService):
    """Mock implementation of IDataFormattingService for testing."""

    def __init__(self, formatting_results: Optional[Dict] = None):
        """Initialize mock data formatting service.

        Args:
            formatting_results: Dictionary containing formatting results
        """
        self._formatting_results = formatting_results or {}

    def format_account_id(self, account_number: str) -> str:
        """Format account number for display."""
        return self._formatting_results.get('account_id', account_number)

    def _convert_metadata_to_highlights_dict(self, statistical_metadata: StatisticalMetadata) -> Dict[str, List[str]]:
        """Convert statistical metadata to highlights dictionary."""
        return self._formatting_results.get('highlights', {})

class MockStatisticalAnalysisService(IStatisticalAnalysisService):
    """Mock implementation of IStatisticalAnalysisService for testing."""

    def compute_statistical_metadata(
        self,
        datatables_responses: Dict[str, AccountResponse],
        algorithms: List[str],
        direction: Optional[str] = None
    ) -> StatisticalMetadata:
        """Compute statistical metadata for processing results."""
        return StatisticalMetadata(highlights=[])

class DrilldownTestFactory:
    """Factory for creating DrilldownResponseService with test doubles."""

    @staticmethod
    def create_drilldown_response_service(
        id_mappings: Optional[Dict] = None,
        cache_data: Optional[Dict] = None,
        formatting_results: Optional[Dict] = None
    ) -> DrilldownResponseService:
        """Create DrilldownResponseService with mock dependencies.

        Args:
            id_mappings: Dictionary containing ID mappings
            cache_data: Dictionary containing cached data
            formatting_results: Dictionary containing formatting results

        Returns:
            DrilldownResponseService instance with mock dependencies
        """
        return DrilldownResponseService(
            id_mapping_service=MockIdMappingService(id_mappings),
            cache_service=MockCacheService(cache_data),
            data_formatting_service=MockDataFormattingService(formatting_results),
            statistical_analysis_service=MockStatisticalAnalysisService()
        )

    @staticmethod
    def create_with_real_dependencies() -> DrilldownResponseService:
        """Create DrilldownResponseService with real dependencies for integration testing.

        Returns:
            DrilldownResponseService instance with real dependencies
        """
        from whatsthedamage.services.id_mapping_service import IdMappingService
        from whatsthedamage.services.cache_service import CacheService
        from whatsthedamage.services.response_formatting_service import ResponseFormattingService
        from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
        from flask_caching import Cache
        from flask import Flask
        from whatsthedamage.models.dt_models import ProcessingResponse
        from typing import Optional

        # Create Flask app and cache for real dependencies
        app = Flask(__name__)
        flask_cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

        # Create adapter to convert Flask Cache to CacheProtocol
        class FlaskCacheAdapter:
            """Adapter to make Flask Cache compatible with CacheProtocol."""

            def __init__(self, cache: Cache):
                self._cache = cache

            def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
                """Store value in cache with timeout."""
                self._cache.set(key, value, timeout=timeout)

            def get(self, key: str) -> Optional[ProcessingResponse]:
                """Retrieve value from cache."""
                return self._cache.get(key)

            def delete(self, key: str) -> None:
                """Remove value from cache."""
                self._cache.delete(key)

        cache_adapter = FlaskCacheAdapter(flask_cache)

        # Create real service instances
        id_mapping_service = IdMappingService(flask_cache)
        cache_service = CacheService(cache_adapter)
        data_formatting_service = ResponseFormattingService()
        statistical_analysis_service = StatisticalAnalysisService(
            enabled_algorithms=['iqr', 'pareto']
        )

        return DrilldownResponseService(
            id_mapping_service=id_mapping_service,
            cache_service=cache_service,
            data_formatting_service=data_formatting_service,
            statistical_analysis_service=statistical_analysis_service
        )
