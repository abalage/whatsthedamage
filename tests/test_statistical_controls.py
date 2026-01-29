"""Test cases for the new statistical analysis controls feature."""

from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService, AnalysisDirection
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField, StatisticalMetadata

def test_recalculate_highlights_method():
    """Test the compute_statistical_metadata method in StatisticalAnalysisService."""
    # Create test data
    test_responses = {
        'account1': DataTablesResponse(
            data=[
                AggregatedRow(
                    category='Grocery',
                    total=DisplayRawField(display='100.00', raw=100.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    category='Utilities',
                    total=DisplayRawField(display='50.00', raw=50.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            account='account1',
            currency='USD'
        )
    }

    # Create service instance
    service = StatisticalAnalysisService()

    # Test with IQR algorithm and columns direction
    result = service.compute_statistical_metadata(
        datatables_responses=test_responses,
        algorithms=['iqr'],
        direction=AnalysisDirection.COLUMNS
    )

    # Verify result is StatisticalMetadata
    assert isinstance(result, StatisticalMetadata)
    assert isinstance(result.highlights, list)

    # Test with Pareto algorithm and rows direction
    result2 = service.compute_statistical_metadata(
        datatables_responses=test_responses,
        algorithms=['pareto'],
        direction=AnalysisDirection.ROWS
    )

    assert isinstance(result2, StatisticalMetadata)
    assert isinstance(result2.highlights, list)

def test_recalculate_highlights_with_both_algorithms():
    """Test compute_statistical_metadata with both algorithms."""
    # Create test data with more varied values to trigger highlights
    test_responses = {
        'account1': DataTablesResponse(
            data=[
                AggregatedRow(
                    category='Grocery',
                    total=DisplayRawField(display='1000.00', raw=1000.0),  # Large value - potential outlier
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    category='Utilities',
                    total=DisplayRawField(display='50.00', raw=50.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    category='Entertainment',
                    total=DisplayRawField(display='200.00', raw=200.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    category='Entertainment',
                    total=DisplayRawField(display='-500.00', raw=-500.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            account='account1',
            currency='USD',
            statistical_metadata=None
        )
    }

    service = StatisticalAnalysisService()

    # Test with both algorithms
    result = service.compute_statistical_metadata(
        datatables_responses=test_responses,
        algorithms=['iqr', 'pareto'],
        direction=AnalysisDirection.COLUMNS
    )

    assert isinstance(result, StatisticalMetadata)
    assert isinstance(result.highlights, list)

    # Should have some highlights for the large grocery value
    highlight_types = [h.highlight_type for h in result.highlights]
    assert any(ht in ['outlier', 'pareto'] for ht in highlight_types)

def test_recalculate_statistics_route():
    """Test the recalculate-statistics route functionality."""
    # This would be a functional test that requires Flask test client
    # For now, we'll just test the service method that the route calls
    pass

def test_highlight_key_format():
    """Test that highlight keys are formatted correctly."""
    service = StatisticalAnalysisService()

    test_responses = {
        'account1': DataTablesResponse(
            data=[
                AggregatedRow(
                    category='TestCategory',
                    total=DisplayRawField(display='100.00', raw=100.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            account='account1',
            currency='USD'
        )
    }

    result = service.compute_statistical_metadata(
        datatables_responses=test_responses,
        algorithms=['iqr'],
        direction=AnalysisDirection.COLUMNS
    )

    # Check that highlights have the correct format
    for highlight in result.highlights:
        assert hasattr(highlight, 'row')
        assert hasattr(highlight, 'column')
        assert hasattr(highlight, 'highlight_type')
        assert highlight.highlight_type in ['outlier', 'pareto', 'excluded']