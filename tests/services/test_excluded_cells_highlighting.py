"""Test for excluded cells highlighting feature."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.exclusion_service import ExclusionService
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField, DetailRow

@pytest.fixture
def sample_dt_response():
    """Create a sample DataTablesResponse with calculated rows and excluded categories."""
    # Create some detail rows
    details1 = [
        DetailRow(
            date=DateField(display="2023-01-15", timestamp=1673779200),
            amount=DisplayRawField(display="100.00", raw=100.0),
            merchant="Grocery Store",
            currency="EUR",
            account="12345678"
        )
    ]

    details2 = [
        DetailRow(
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
            category="Grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            month=DateField(display="January 2023", timestamp=1672531200),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details1,
            is_calculated=False
        ),
        AggregatedRow(
            category="Rent",
            total=DisplayRawField(display="500.00", raw=500.0),
            month=DateField(display="January 2023", timestamp=1672531200),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details2,
            is_calculated=False
        ),
        AggregatedRow(
            category="Utilities",
            total=DisplayRawField(display="200.00", raw=200.0),
            month=DateField(display="February 2023", timestamp=1677657600),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=[],
            is_calculated=False
        )
    ]

    # Create calculated rows (Balance and Total)
    calculated_rows = [
        AggregatedRow(
            category="Balance",
            total=DisplayRawField(display="600.00", raw=600.0),
            month=DateField(display="January 2023", timestamp=1672531200),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        ),
        AggregatedRow(
            category="Total",
            total=DisplayRawField(display="800.00", raw=800.0),
            month=DateField(display="Total", timestamp=0),
            date=DateField(display="Total", timestamp=0),
            details=[],
            is_calculated=True
        )
    ]

    # Combine all rows
    all_rows = regular_rows + calculated_rows

    return DataTablesResponse(
        data=all_rows,
        account="12345678",
        currency="EUR"
    )

def test_excluded_cells_highlighting_with_exclusion_service(sample_dt_response):
    """Test that excluded cells are properly highlighted."""
    # Create exclusion service with some excluded categories
    exclusion_service = ExclusionService()
    exclusion_service.set_user_exclusions("default", ["Rent", "Deposit"])

    # Create statistical analysis service with exclusion service
    statistical_service = StatisticalAnalysisService(
        enabled_algorithms=["iqr", "pareto"],
        exclusion_service=exclusion_service
    )

    # Compute statistical metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": sample_dt_response
    })

    # Check that we have highlights
    assert len(metadata.highlights) > 0

    # Find excluded highlights
    excluded_highlights = [
        h for h in metadata.highlights
        if h.highlight_type == "excluded"
    ]

    # Should have excluded highlights for:
    # 1. Calculated rows (Balance, Total)
    # 2. Excluded categories (Rent)
    assert len(excluded_highlights) > 0

    # Check that calculated rows are excluded
    calculated_excluded = [
        h for h in excluded_highlights
        if h.row in ["Balance", "Total"]
    ]
    assert len(calculated_excluded) > 0

    # Check that excluded categories are excluded
    category_excluded = [
        h for h in excluded_highlights
        if h.row == "Rent"
    ]
    assert len(category_excluded) > 0

    # Verify the highlight structure
    for highlight in excluded_highlights:
        assert hasattr(highlight, 'row')
        assert hasattr(highlight, 'column')
        assert hasattr(highlight, 'highlight_type')
        assert highlight.highlight_type == "excluded"

def test_excluded_cells_highlighting_without_exclusion_service(sample_dt_response):
    """Test that calculated rows are still excluded even without exclusion service."""
    # Create statistical analysis service without exclusion service
    statistical_service = StatisticalAnalysisService(
        enabled_algorithms=["iqr", "pareto"],
        exclusion_service=None
    )

    # Compute statistical metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": sample_dt_response
    })

    # Find excluded highlights
    excluded_highlights = [
        h for h in metadata.highlights
        if h.highlight_type == "excluded"
    ]

    # Should have excluded highlights for calculated rows
    assert len(excluded_highlights) > 0

    # Check that calculated rows are excluded
    calculated_excluded = [
        h for h in excluded_highlights
        if h.row in ["Balance", "Total"]
    ]
    assert len(calculated_excluded) > 0

def test_get_excluded_cell_highlights_method(sample_dt_response):
    """Test the _get_excluded_cell_highlights method directly."""
    # Create exclusion service
    exclusion_service = ExclusionService()
    exclusion_service.set_user_exclusions("default", ["Rent"])

    # Create statistical analysis service
    statistical_service = StatisticalAnalysisService(
        exclusion_service=exclusion_service
    )

    # Call the method directly
    excluded_highlights = statistical_service._get_excluded_cell_highlights(sample_dt_response)

    # Should have excluded highlights
    assert len(excluded_highlights) > 0

    # Check that we have highlights for calculated rows
    calculated_highlights = [
        h for h in excluded_highlights
        if h.row in ["Balance", "Total"]
    ]
    assert len(calculated_highlights) > 0

    # Check that we have highlights for excluded categories
    category_highlights = [
        h for h in excluded_highlights
        if h.row == "Rent"
    ]
    assert len(category_highlights) > 0

    # Verify all highlights have the correct type
    for highlight in excluded_highlights:
        assert highlight.highlight_type == "excluded"
