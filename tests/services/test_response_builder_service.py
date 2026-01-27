"""Tests for ResponseBuilderService.

Streamlined tests focusing on critical functionality using parameterized tests
for better maintainability and overview.
"""
import pytest
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.models.api_models import ProcessingRequest, DetailedResponse
from whatsthedamage.config.dt_models import AggregatedRow, DisplayRawField, DateField, DataTablesResponse


@pytest.fixture
def service():
    """Create ResponseBuilderService instance."""
    return ResponseBuilderService()


class TestApiResponseBuilding:
    """Test API response building."""

    def test_builds_detailed_response_with_transactions(self, service):
        """Test building detailed response with transaction data."""
        agg_rows = [
            AggregatedRow(
                category="grocery",
                month=DateField(display="2024-01", timestamp=1704067200),
                date=DateField(display="2024-01", timestamp=1704067200),
                total=DisplayRawField(display="150.50 HUF", raw=150.50),
                details=[]
            )
        ]
        dt_response = DataTablesResponse(data=agg_rows)
        dt_response.account = "ACC123"  # Set account ID
        dt_response.currency = "HUF"  # Set currency

        # Create dict of responses by account ID
        datatables_dict = {"ACC123": dt_response}

        params = ProcessingRequest(ml_enabled=True)
        metadata = {'row_count': 150}

        response = service.build_api_detailed_response(
            datatables_response=datatables_dict,
            metadata=metadata,
            params=params,
            processing_time=1.2
        )

        assert isinstance(response, DetailedResponse)
        assert len(response.data) == 1
        assert response.data[0].category == "grocery"
        assert response.metadata.row_count == 150


# Note: Error response building tests are covered by integration tests
# (test_api_v1_endpoints.py, test_api_v2_endpoints.py, test_routes.py)
# which provide Flask app context. Unit testing error responses in isolation
# requires mocking Flask's jsonify(), which adds complexity without value.


class TestDateRangeBuilding:
    """Test date range building helper."""

    @pytest.mark.parametrize("start_date,end_date,expected", [
        ("2024.01.01", "2024.12.31", {'start': '2024.01.01', 'end': '2024.12.31'}),
        ("2024.01.01", None, {'start': '2024.01.01'}),
        (None, "2024.12.31", {'end': '2024.12.31'}),
        (None, None, None),
    ])
    def test_builds_date_range(self, service, start_date, end_date, expected):
        """Test building date ranges with various combinations."""
        params = ProcessingRequest(start_date=start_date, end_date=end_date)

        date_range = service._build_date_range(params)

        assert date_range == expected


class TestIntegration:
    """Integration test for complete workflows."""
