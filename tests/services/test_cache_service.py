"""Tests for CacheService and cache functionality."""

import pytest
from whatsthedamage.services.cache_service import CacheService, CacheProtocol
from whatsthedamage.models.dt_models import ProcessingResponse, DataTablesResponse, StatisticalMetadata, AggregatedRow, CellHighlight, DisplayRawField, DateField, DetailRow
from typing import Dict, Optional
import time
import uuid

class MockCacheBackend:
    """Mock cache backend implementing CacheProtocol for testing."""

    def __init__(self):
        self._store: Dict[str, ProcessingResponse] = {}
        self._expiry_times: Dict[str, float] = {}

    def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
        self._store[key] = value
        self._expiry_times[key] = time.time() + timeout

    def get(self, key: str) -> Optional[ProcessingResponse]:
        if key not in self._store:
            return None

        if time.time() > self._expiry_times[key]:
            return None

        return self._store[key]

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
        if key in self._expiry_times:
            del self._expiry_times[key]

class TestCacheProtocol:
    """Tests for CacheProtocol compliance."""

    def test_mock_cache_implements_protocol(self):
        """Test that MockCacheBackend implements CacheProtocol."""
        cache = MockCacheBackend()
        assert isinstance(cache, CacheProtocol)

    def test_cache_protocol_methods(self):
        """Test that cache protocol methods work correctly."""
        cache = MockCacheBackend()

        # Test data
        test_result = ProcessingResponse(
            result_id="test-id",
            data={},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

        # Test set and get
        cache.set("test_key", test_result, timeout=60)
        retrieved = cache.get("test_key")
        assert retrieved is not None
        assert retrieved == test_result

        # Test delete
        cache.delete("test_key")
        assert cache.get("test_key") is None

class TestCacheService:
    """Tests for CacheService functionality."""

    @pytest.fixture
    def cache_backend(self):
        """Fixture for mock cache backend."""
        return MockCacheBackend()

    @pytest.fixture
    def cache_service(self, cache_backend):
        """Fixture for cache service with default TTL."""
        return CacheService(cache_backend)

    @pytest.fixture
    def sample_cached_result(self):
        """Fixture for sample cached processing result."""
        row_id_sample=str(uuid.uuid4())
        return ProcessingResponse(
            result_id="test-result-id",
            data={
                "account1": DataTablesResponse(
                    data=[
                        AggregatedRow(
                            row_id=row_id_sample,
                            category="Grocery",
                            total=DisplayRawField(display="100.00", raw=100.0),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        )
                    ],
                    account="account1",
                    currency="USD",
                    metadata=None
                )
            },
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[
                CellHighlight(row_id=row_id_sample, highlight_type="outlier")
            ])
        )

    def test_cache_service_initialization(self, cache_backend):
        """Test CacheService initialization with custom TTL."""
        service = CacheService(cache_backend, ttl=300)
        assert service._ttl == 300

    def test_cache_service_set_and_get(self, cache_service, sample_cached_result):
        """Test setting and getting cached results."""
        # Set cache
        cache_service.set("test_result_id", sample_cached_result)

        # Get cache
        retrieved = cache_service.get("test_result_id")
        assert retrieved is not None
        assert retrieved == sample_cached_result
        assert retrieved.data["account1"].account == "account1"

    def test_cache_service_get_nonexistent(self, cache_service):
        """Test getting non-existent cache entry."""
        result = cache_service.get("nonexistent_key")
        assert result is None

    def test_cache_service_delete(self, cache_service, sample_cached_result):
        """Test deleting cache entries."""
        # Set and verify
        cache_service.set("test_key", sample_cached_result)
        assert cache_service.get("test_key") is not None

        # Delete and verify
        cache_service.delete("test_key")
        assert cache_service.get("test_key") is None

    def test_cache_service_delete_nonexistent(self, cache_service):
        """Test deleting non-existent cache entry (should not raise error)."""
        cache_service.delete("nonexistent_key")  # Should not raise

    def test_cache_service_with_different_ttl(self):
        """Test cache service with different TTL values."""
        backend = MockCacheBackend()
        short_ttl_service = CacheService(backend, ttl=1)  # 1 second
        long_ttl_service = CacheService(backend, ttl=3600)  # 1 hour

        sample_result = ProcessingResponse(
            result_id="test-id",
            data={},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

        # Set with short TTL
        short_ttl_service.set("short_key", sample_result)
        # Set with long TTL
        long_ttl_service.set("long_key", sample_result)

        # Both should be available immediately
        assert short_ttl_service.get("short_key") is not None
        assert long_ttl_service.get("long_key") is not None

class TestCacheExpiry:
    """Tests for cache expiry functionality."""

    @pytest.fixture
    def cache_service(self):
        """Fixture for cache service with short TTL for testing."""
        backend = MockCacheBackend()
        return CacheService(backend, ttl=1)  # 1 second TTL

    @pytest.fixture
    def sample_result(self):
        """Fixture for minimal sample result."""
        return ProcessingResponse(
            result_id="test-id",
            data={},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

    def test_cache_expiry_after_ttl(self, cache_service, sample_result):
        """Test that cache expires after TTL."""
        # Set cache
        cache_service.set("expiry_test", sample_result)
        assert cache_service.get("expiry_test") is not None

        # Wait for expiry
        time.sleep(1.1)  # Sleep slightly more than TTL

        # Should be expired
        assert cache_service.get("expiry_test") is None

    def test_cache_still_valid_before_ttl(self, cache_service, sample_result):
        """Test that cache is still valid just before TTL."""
        # Set cache
        cache_service.set("valid_test", sample_result)
        assert cache_service.get("valid_test") is not None

        # Wait most of TTL
        time.sleep(0.5)  # Half of 1 second TTL

        # Should still be valid
        assert cache_service.get("valid_test") is not None

    def test_cache_expiry_with_multiple_entries(self, cache_service, sample_result):
        """Test expiry with multiple cache entries."""
        # Set multiple entries with different TTLs
        cache_service.set("entry1", sample_result)  # 1 second TTL
        cache_service.set("entry2", sample_result)  # 1 second TTL

        # Both should be available
        assert cache_service.get("entry1") is not None
        assert cache_service.get("entry2") is not None

        # Wait for expiry
        time.sleep(1.1)

        # Both should be expired
        assert cache_service.get("entry1") is None
        assert cache_service.get("entry2") is None

class TestCacheServiceIntegration:
    """Integration tests for CacheService."""

    def test_cache_service_with_real_data_structures(self):
        """Test cache service with realistic data structures."""
        backend = MockCacheBackend()
        service = CacheService(backend)

        # Create realistic test data
        detail_rows = [
            DetailRow(
                row_id=str(uuid.uuid4()),
                date=DateField(display="2023-01-01", timestamp=1672531200),
                amount=DisplayRawField(display="50.00", raw=50.0),
                merchant="Grocery Store",
                currency="USD",
                account="checking"
            )
        ]

        row_id_utiilities=str(uuid.uuid4())
        aggregated_rows = [
            AggregatedRow(
                row_id=str(uuid.uuid4()),
                category="Grocery",
                total=DisplayRawField(display="100.00", raw=100.0),
                date=DateField(display="Jan 2023", timestamp=1672531200),
                details=detail_rows,
                is_calculated=False
            ),
            AggregatedRow(
                row_id=str(uuid.uuid4()),
                category="Utilities",
                total=DisplayRawField(display="150.00", raw=150.0),
                date=DateField(display="Jan 2023", timestamp=1672531200),
                details=[],
                is_calculated=False
            )
        ]

        dt_response = DataTablesResponse(
            data=aggregated_rows,
            account="checking",
            currency="USD",
            metadata=None
        )

        cached_result = ProcessingResponse(
            result_id="test-result-id",
            data={"checking": dt_response},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[
                CellHighlight(row_id=row_id_utiilities, highlight_type="outlier")
            ])
        )

        # Test caching and retrieval
        service.set("realistic_test", cached_result)
        retrieved = service.get("realistic_test")

        assert retrieved is not None
        assert len(retrieved.data) == 1
        assert retrieved.data["checking"].account == "checking"
        assert len(retrieved.data["checking"].data) == 2
        assert len(retrieved.statistical_metadata.highlights) == 1

    def test_cache_service_with_multiple_accounts(self):
        """Test cache service with multiple account responses."""
        backend = MockCacheBackend()
        service = CacheService(backend)

        # Create responses for multiple accounts
        account1_response = DataTablesResponse(
            data=[AggregatedRow(
                row_id=str(uuid.uuid4()),
                category="Grocery",
                total=DisplayRawField(display="100.00", raw=100.0),
                date=DateField(display="Jan 2023", timestamp=1672531200),
                details=[],
                is_calculated=False
            )],
            account="account1",
            currency="USD"
        )

        account2_response = DataTablesResponse(
            data=[AggregatedRow(
                row_id=str(uuid.uuid4()),
                category="Rent",
                total=DisplayRawField(display="1000.00", raw=1000.0),
                date=DateField(display="Jan 2023", timestamp=1672531200),
                details=[],
                is_calculated=False
            )],
            account="account2",
            currency="EUR"
        )

        cached_result = ProcessingResponse(
            result_id="test-result-id",
            data={
                "account1": account1_response,
                "account2": account2_response
            },
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

        # Test caching and retrieval
        service.set("multi_account_test", cached_result)
        retrieved = service.get("multi_account_test")

        assert retrieved is not None
        assert len(retrieved.data) == 2
        assert "account1" in retrieved.data
        assert "account2" in retrieved.data
        assert retrieved.data["account1"].currency == "USD"
        assert retrieved.data["account2"].currency == "EUR"

class TestCacheServiceErrorHandling:
    """Tests for error handling in CacheService."""

    def test_cache_service_with_failing_backend(self):
        """Test cache service with backend that raises exceptions."""
        class FailingCacheBackend:
            def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
                raise RuntimeError("Backend failure")

            def get(self, key: str) -> Optional[ProcessingResponse]:
                raise RuntimeError("Backend failure")

            def delete(self, key: str) -> None:
                raise RuntimeError("Backend failure")

        backend = FailingCacheBackend()
        service = CacheService(backend)

        sample_result = ProcessingResponse(
            result_id="test-id",
            data={},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

        # These should propagate the exceptions
        with pytest.raises(RuntimeError, match="Backend failure"):
            service.set("test_key", sample_result)

        with pytest.raises(RuntimeError, match="Backend failure"):
            service.get("test_key")

        with pytest.raises(RuntimeError, match="Backend failure"):
            service.delete("test_key")

    def test_cache_service_with_partial_failure(self):
        """Test cache service where some operations fail."""
        class PartialFailingCacheBackend:
            def __init__(self):
                self.fail_get = False

            def set(self, key: str, value: ProcessingResponse, timeout: int) -> None:
                pass  # Always works

            def get(self, key: str) -> Optional[ProcessingResponse]:
                if self.fail_get:
                    raise RuntimeError("Get failed")
                return None

            def delete(self, key: str) -> None:
                pass  # Always works

        backend = PartialFailingCacheBackend()
        service = CacheService(backend)

        sample_result = ProcessingResponse(
            result_id="test-id",
            data={},
            metadata=None,
            statistical_metadata=StatisticalMetadata(highlights=[])
        )

        # Set should work
        service.set("test_key", sample_result)

        # Get should fail when configured to fail
        backend.fail_get = True
        with pytest.raises(RuntimeError, match="Get failed"):
            service.get("test_key")

        # Delete should work
        service.delete("test_key")
