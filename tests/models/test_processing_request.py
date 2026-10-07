"""Tests for ProcessingRequest model with csv_profile_id parameter."""

import pytest
from whatsthedamage.models.api.requests import ProcessingRequest


class TestProcessingRequestCsvProfileId:
    """Tests for ProcessingRequest csv_profile_id field."""

    def test_processing_request_default_csv_profile_id_is_none(self):
        """Test that ProcessingRequest has csv_profile_id=None by default."""
        request = ProcessingRequest()
        assert request.csv_profile_id is None

    def test_processing_request_with_csv_profile_id_otp_hu(self):
        """Test ProcessingRequest with csv_profile_id='otp-hu'."""
        request = ProcessingRequest(csv_profile_id='otp-hu')
        assert request.csv_profile_id == 'otp-hu'

    def test_processing_request_with_csv_profile_id_kh_hu(self):
        """Test ProcessingRequest with csv_profile_id='kh-hu'."""
        request = ProcessingRequest(csv_profile_id='kh-hu')
        assert request.csv_profile_id == 'kh-hu'

    def test_processing_request_with_csv_profile_id_custom_value(self):
        """Test ProcessingRequest with custom csv_profile_id value."""
        request = ProcessingRequest(csv_profile_id='custom-profile')
        assert request.csv_profile_id == 'custom-profile'

    def test_processing_request_with_all_fields_including_csv_profile_id(self):
        """Test ProcessingRequest with all fields including csv_profile_id."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            end_date="2024.12.31",
            ml_enabled=True,
            category_filter="grocery",
            date_format="%Y.%m.%d",
            csv_profile_id='otp-hu'
        )
        assert request.start_date == "2024.01.01"
        assert request.end_date == "2024.12.31"
        assert request.ml_enabled is True
        assert request.category_filter == "grocery"
        assert request.date_format == "%Y.%m.%d"
        assert request.csv_profile_id == 'otp-hu'

    def test_processing_request_csv_profile_id_none_with_other_fields(self):
        """Test ProcessingRequest with csv_profile_id=None and other fields set."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            ml_enabled=True,
            csv_profile_id=None
        )
        assert request.csv_profile_id is None
        assert request.start_date == "2024.01.01"
        assert request.ml_enabled is True


class TestProcessingRequestCsvProfileIdWithDateValidation:
    """Tests for ProcessingRequest csv_profile_id with date validation."""

    def test_csv_profile_id_with_valid_dates(self):
        """Test csv_profile_id works with valid date range."""
        request = ProcessingRequest(
            start_date="2024.01.01",
            end_date="2024.12.31",
            csv_profile_id='otp-hu'
        )
        assert request.csv_profile_id == 'otp-hu'
        assert request.start_date == "2024.01.01"
        assert request.end_date == "2024.12.31"

    def test_csv_profile_id_with_invalid_date_range_raises_error(self):
        """Test that invalid date range raises ValidationError regardless of csv_profile_id."""
        with pytest.raises(Exception) as exc_info:
            ProcessingRequest(
                start_date="2024.12.31",
                end_date="2024.01.01",
                csv_profile_id='otp-hu'
            )
        assert "Start date must be before or equal to end date" in str(exc_info.value)

    def test_csv_profile_id_with_invalid_start_date_raises_error(self):
        """Test that invalid start_date raises ValidationError regardless of csv_profile_id."""
        with pytest.raises(Exception) as exc_info:
            ProcessingRequest(
                start_date="not-a-date",
                csv_profile_id=None
            )
        assert "must be in %Y.%m.%d format" in str(exc_info.value)
