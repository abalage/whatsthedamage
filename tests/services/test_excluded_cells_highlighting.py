"""Test for excluded cells highlighting feature."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService

from whatsthedamage.models.domain.dt_models import AccountResponse, AggregatedRow, DisplayRawField, DateField, DetailRow
import uuid

@pytest.fixture
def sample_dt_response():
    """Create a sample AccountResponse with calculated rows and excluded categories."""
    # Create some detail rows
    details1 = [
        DetailRow(
            row_id=str(uuid.uuid4()),
            date=DateField(display="2023-01-15", timestamp=1673779200),
            amount=DisplayRawField(display="100.00", raw=100.0),
            merchant="Grocery Store",
            currency="EUR",
            account="12345678"
        )
    ]

    details2 = [
        DetailRow(
            row_id=str(uuid.uuid4()),
            date=DateField(display="2023-01-10", timestamp=1673347200),
            amount=DisplayRawField(display="500.00", raw=500.0),
            merchant="Landlord",
            currency="EUR",
            account="12345678"
        )
    ]

    # Create regular rows
    regular_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details1,
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Rent",
            total=DisplayRawField(display="500.00", raw=500.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details2,
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Utilities",
            total=DisplayRawField(display="200.00", raw=200.0),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=[],
            is_calculated=False
        )
    ]

    # Create calculated rows (Balance and Total)
    calculated_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Balance",
            total=DisplayRawField(display="600.00", raw=600.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Total",
            total=DisplayRawField(display="800.00", raw=800.0),
            date=DateField(display="Total", timestamp=0),
            details=[],
            is_calculated=True
        )
    ]

    # Combine all rows
    all_rows = regular_rows + calculated_rows

    return AccountResponse(
        data=all_rows,
        account="12345678",
        currency="EUR"
    )

def test_excluded_cells_highlighting_with_exclusion_service(sample_dt_response):
    """Test that excluded cells are properly highlighted."""
    # Create statistical analysis service
    statistical_service = StatisticalAnalysisService(
        enabled_algorithms=["iqr", "pareto"]
    )

    # Set user exclusions directly on the service
    statistical_service.set_user_exclusions("default", ["Rent", "Deposit"])

    # Compute statistical metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": sample_dt_response
    })

    # Check that we have highlights
    assert len(metadata.highlights) > 0

    # Find excluded highlights
    excluded_highlights = [
        h for h in metadata.highlights
        if h.highlight_types[0] == "excluded"
    ]

    # Should have excluded highlights for:
    # 1. Calculated rows (Balance, Total)
    # 2. Excluded categories (Rent)
    assert len(excluded_highlights) > 0

    # Verify the highlight structure
    for highlight in excluded_highlights:
        assert hasattr(highlight, 'row_id')
        assert hasattr(highlight, 'highlight_types')
        assert highlight.highlight_types[0] == "excluded"

def test_excluded_cells_highlighting_without_exclusion_service(sample_dt_response):
    """Test that calculated rows are still excluded even without exclusion service."""
    # Create statistical analysis service without setting any user exclusions
    statistical_service = StatisticalAnalysisService(
        enabled_algorithms=["iqr", "pareto"]
    )

    # Compute statistical metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": sample_dt_response
    })

    # Find excluded highlights
    excluded_highlights = [
        h for h in metadata.highlights
        if h.highlight_types[0] == "excluded"
    ]

    # Should have excluded highlights for calculated rows
    assert len(excluded_highlights) > 0

    # # Check that calculated rows are excluded
    # calculated_excluded = [
    #     h for h in excluded_highlights
    #     if h.row in ["Balance", "Total"]
    # ]
    # assert len(calculated_excluded) > 0

def test_get_excluded_cell_highlights_method(sample_dt_response):
    """Test the _get_excluded_cell_highlights method directly."""
    # Create statistical analysis service
    statistical_service = StatisticalAnalysisService()
    statistical_service.set_user_exclusions("default", ["Rent"])

    # Call the method directly
    excluded_highlights = statistical_service._get_excluded_cell_highlights(sample_dt_response)

    # Should have excluded highlights
    assert len(excluded_highlights) > 0

    # Verify all highlights have the correct type
    for highlight in excluded_highlights:
        assert highlight.highlight_types[0] == "excluded"
