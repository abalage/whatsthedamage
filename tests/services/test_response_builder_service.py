"""Tests for ResponseBuilderService.

Streamlined tests focusing on critical functionality using parameterized tests
for better maintainability and overview.
"""
import pytest
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.models.api_models import ProcessingRequest, SummaryResponse, DetailedResponse
from whatsthedamage.config.dt_models import AggregatedRow, DisplayRawField, DateField, DataTablesResponse


@pytest.fixture
def service():
    """Create ResponseBuilderService instance."""
    return ResponseBuilderService()


class TestApiResponseBuilding:
    """Test API response building (v1 summary and v2 detailed)."""

    @pytest.mark.parametrize("ml_enabled,start_date,end_date,expected_date_range", [
        (True, "2024.01.01", "2024.12.31", {'start': '2024.01.01', 'end': '2024.12.31'}),
        (False, "2024.01.01", None, {'start': '2024.01.01'}),
        (True, None, "2024.12.31", {'end': '2024.12.31'}),
        (False, None, None, None),
    ])
    def test_builds_summary_response_with_various_params(
        self, service, ml_enabled, start_date, end_date, expected_date_range
    ):
        """Test building summary responses with different parameter combinations."""
        params = ProcessingRequest(
            ml_enabled=ml_enabled,
            start_date=start_date,
            end_date=end_date
        )
        data = {'grocery': 150.0, 'utilities': 80.0}
        metadata = {'row_count': 25}

        response = service.build_api_summary_response(
            data=data, metadata=metadata, params=params, processing_time=0.5
        )

        assert isinstance(response, SummaryResponse)
        assert response.data == data
        assert response.metadata.row_count == 25
        assert response.metadata.ml_enabled == ml_enabled
        assert response.metadata.date_range == expected_date_range

    def test_builds_detailed_response_with_transactions(self, service):
        """Test building detailed response with transaction data."""
        agg_rows = [
            AggregatedRow(
                category="grocery",
                month=DateField(display="2024-01", timestamp=1704067200),
                total=DisplayRawField(display="150.50 HUF", raw=150.50),
                details=[]
            )
        ]
        dt_response = DataTablesResponse(data=agg_rows)
        params = ProcessingRequest(ml_enabled=True)
        metadata = {'row_count': 150}

        response = service.build_api_detailed_response(
            datatables_response=dt_response,
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


class TestTableParsingForRendering:
    """Test HTML table parsing and metadata extraction."""

    @pytest.mark.parametrize("html,expected_headers,expected_cell_values", [
        # Simple table
        ("""
        <table>
            <thead><tr><th>Categories</th><th>Amount</th></tr></thead>
            <tbody><tr><th>Grocery</th><td>150.50</td></tr></tbody>
        </table>
        """, ["Categories", "Amount"], [("Grocery", None), ("150.50", 150.50)]),
        
        # Currency with symbols
        ("""
        <table>
            <thead><tr><th>Categories</th><th>Total</th></tr></thead>
            <tbody><tr><th>Utilities</th><td>-80.75 HUF</td></tr></tbody>
        </table>
        """, ["Categories", "Total"], [("Utilities", None), ("-80.75 HUF", -80.75)]),
        
        # Empty cells
        ("""
        <table>
            <thead><tr><th>Categories</th><th>Amount</th></tr></thead>
            <tbody><tr><th>Other</th><td></td></tr></tbody>
        </table>
        """, ["Categories", "Amount"], [("Other", None), ("", 0)]),
    ])
    def test_parses_html_tables_with_various_content(
        self, service, html, expected_headers, expected_cell_values
    ):
        """Test parsing HTML tables with different content patterns."""
        headers, rows = service.prepare_table_for_rendering(html)

        assert headers == expected_headers
        assert len(rows) == 1
        for i, (expected_display, expected_order) in enumerate(expected_cell_values):
            assert rows[0][i]['display'] == expected_display
            if expected_order is None:
                assert rows[0][i]['order'] is None
            elif expected_order == 0:
                assert rows[0][i]['order'] == 0
            else:
                assert abs(rows[0][i]['order'] - expected_order) < 0.01

    def test_first_column_not_sortable(self, service):
        """Test that first column (categories) has no numeric order."""
        html = """
        <table>
            <thead><tr><th>Categories</th><th>Amount</th></tr></thead>
            <tbody><tr><th>Test</th><td>100.00</td></tr></tbody>
        </table>
        """

        _, rows = service.prepare_table_for_rendering(html)

        assert rows[0][0]['order'] is None  # Categories column
        assert abs(rows[0][1]['order'] - 100.0) < 0.01  # Amount column


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

    def test_complete_api_workflow(self, service):
        """Test complete API response building workflow."""
        params = ProcessingRequest(
            start_date="2024.01.01",
            end_date="2024.12.31",
            ml_enabled=True
        )
        data = {'grocery': 150.0}
        metadata = {'row_count': 25}

        # Build response
        response = service.build_api_summary_response(
            data=data, metadata=metadata, params=params, processing_time=0.5
        )

        # Verify serialization
        response_dict = response.model_dump()
        assert 'data' in response_dict
        assert 'metadata' in response_dict
        assert response_dict['metadata']['ml_enabled'] is True
        assert response_dict['metadata']['row_count'] == 25
