"""Tests for ProcessingRequest model with cache_ttl parameter."""

import pytest
from whatsthedamage.models.api.requests import ProcessingRequest


class TestProcessingRequestCacheTtl:
    """Tests for ProcessingRequest cache_ttl field."""

    def test_processing_request_default_cache_ttl_is_none(self):
        """Test that ProcessingRequest has cache_ttl=None by default."""
        request = ProcessingRequest()
        assert request.cache_ttl is None

    def test_processing_request_with_cache_ttl_1800(self):
        """Test ProcessingRequest with cache_ttl=1800."""
        request = ProcessingRequest(cache_ttl=1800)
        assert request.cache_ttl == 1800

    def test_processing_request_with_cache_ttl_0(self):
        """Test ProcessingRequest with cache_ttl=0 (never expire)."""
        request = ProcessingRequest(cache_ttl=0)
        assert request.cache_ttl == 0

    def test_processing_request_with_cache_ttl_custom_value(self):
        """Test ProcessingRequest with custom cache_ttl value."""
        request = ProcessingRequest(cache_ttl=3600)
        assert request.cache_ttl == 3600

    def test_processing_request_with_all_fields_including_cache_ttl(self):
        """Test ProcessingRequest with all fields including cache_ttl."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            end_date="2024.12.31",
            ml_enabled=True,
            category_filter="grocery",
            date_format="%Y.%m.%d",
            cache_ttl=1800
        )
        assert request.start_date == "2024.01.01"
        assert request.end_date == "2024.12.31"
        assert request.ml_enabled is True
        assert request.category_filter == "grocery"
        assert request.date_format == "%Y.%m.%d"
        assert request.cache_ttl == 1800

    def test_processing_request_cache_ttl_none_with_other_fields(self):
        """Test ProcessingRequest with cache_ttl=None and other fields set."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            ml_enabled=True,
            cache_ttl=None
        )
        assert request.cache_ttl is None
        assert request.start_date == "2024.01.01"
        assert request.ml_enabled is True


class TestProcessingRequestCacheTtlWithDateValidation:
    """Tests for ProcessingRequest cache_ttl with date validation."""

    def test_cache_ttl_with_valid_dates(self):
        """Test cache_ttl works with valid date range."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            end_date="2024.12.31",
            cache_ttl=1800
        )
        assert request.cache_ttl == 1800
        assert request.start_date == "2024.01.01"
        assert request.end_date == "2024.12.31"

    def test_cache_ttl_with_invalid_date_range_raises_error(self):
        """Test that invalid date range raises ValidationError regardless of cache_ttl."""
        with pytest.raises(Exception) as exc_info:
            ProcessingRequest(
                start_date="2024.12.31",
                end_date="2024.01.01",
                cache_ttl=1800
            )
        assert "Start date must be before or equal to end date" in str(exc_info.value)

    def test_cache_ttl_with_invalid_start_date_raises_error(self):
        """Test that invalid start_date raises ValidationError regardless of cache_ttl."""
        with pytest.raises(Exception) as exc_info:
            ProcessingRequest(
                start_date="not-a-date",
                cache_ttl=0
            )
        assert "must be in %Y.%m.%d format" in str(exc_info.value)
