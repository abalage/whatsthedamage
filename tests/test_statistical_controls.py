"""Test cases for the new statistical analysis controls feature."""

from datetime import datetime
from types import SimpleNamespace

from whatsthedamage.services.statistical_analysis_service import (
    StatisticalAnalysisService,
    AnalysisDirection,
)
from whatsthedamage.models.domain.dt_models import (
    AggregatedRow,
    DisplayRawField,
    DateField,
    StatisticalMetadata,
)
from whatsthedamage.models.domain.account import Account
import uuid


def _make_transaction(account, category, amount, year=2024, month=1):
    """Create a Transaction-like object for analysis tests."""
    return SimpleNamespace(
        account=account,
        category_id=category,
        amount=amount,
        date=datetime(year, month, 15),
    )

def test_recalculate_highlights_method():
    """Test the compute_statistical_metadata method in StatisticalAnalysisService."""
    # Create test data
    test_responses = {
        'account1': Account(
            data=[
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Grocery',
                    total=DisplayRawField(display='100.00', raw=100.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Utilities',
                    total=DisplayRawField(display='50.00', raw=50.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            id='account1',
            currency='USD'
        )
    }

    # Create service instance
    service = StatisticalAnalysisService()

    # Test with IQR algorithm and columns direction
    result = service.compute_statistical_metadata(
        account_responses=test_responses,
        algorithms=['iqr'],
        direction=AnalysisDirection.COLUMNS
    )

    # Verify result is StatisticalMetadata
    assert isinstance(result, StatisticalMetadata)
    assert isinstance(result.highlights, list)

    # Test with Pareto algorithm and rows direction
    result2 = service.compute_statistical_metadata(
        account_responses=test_responses,
        algorithms=['pareto'],
        direction=AnalysisDirection.ROWS
    )

    assert isinstance(result2, StatisticalMetadata)
    assert isinstance(result2.highlights, list)

def test_recalculate_highlights_with_both_algorithms():
    """Test compute_statistical_metadata with both algorithms."""
    # Create test data with more varied values to trigger highlights
    test_responses = {
        'account1': Account(
            data=[
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Grocery',
                    total=DisplayRawField(display='1000.00', raw=1000.0),  # Large value - potential outlier
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Utilities',
                    total=DisplayRawField(display='50.00', raw=50.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Entertainment',
                    total=DisplayRawField(display='200.00', raw=200.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                ),
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='Entertainment',
                    total=DisplayRawField(display='-500.00', raw=-500.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            id='account1',
            currency='USD'
        )
    }

    service = StatisticalAnalysisService()

    # Test with both algorithms
    result = service.compute_statistical_metadata(
        account_responses=test_responses,
        algorithms=['iqr', 'pareto'],
        direction=AnalysisDirection.COLUMNS
    )

    assert isinstance(result, StatisticalMetadata)
    assert isinstance(result.highlights, list)

    # Should have some highlights for the large grocery value
    highlight_types = [h.highlight_types[0] for h in result.highlights]
    assert any(ht in ['outlier', 'pareto'] for ht in highlight_types)

def test_compute_highlights_from_transactions_columns_direction():
    """Test Pareto analysis with columns direction (categories within months)."""
    service = StatisticalAnalysisService()
    transactions = [
        _make_transaction('acc1', 'grocery', -100.0),
        _make_transaction('acc1', 'utilities', -50.0),
        _make_transaction('acc1', 'entertainment', -200.0),
    ]

    highlights = service.compute_highlights_from_transactions(
        transactions,
        algorithms=['pareto'],
        direction='columns'
    )

    # Pareto marks entertainment (200) and grocery (100) as top contributors
    assert highlights.get('acc1|2024-01|entertainment') == ['pareto']
    assert highlights.get('acc1|2024-01|grocery') == ['pareto']
    assert 'acc1|2024-01|utilities' not in highlights


def test_compute_highlights_from_transactions_rows_direction():
    """Test IQR analysis with rows direction (months within categories)."""
    service = StatisticalAnalysisService()
    transactions = [
        _make_transaction('acc1', 'grocery', -10.0, month=1),
        _make_transaction('acc1', 'grocery', -11.0, month=2),
        _make_transaction('acc1', 'grocery', -10.0, month=3),
        _make_transaction('acc1', 'grocery', -10.0, month=4),
        # Far outlier for the grocery category
        _make_transaction('acc1', 'grocery', -1000.0, month=5),
    ]

    highlights = service.compute_highlights_from_transactions(
        transactions,
        algorithms=['iqr'],
        direction='rows'
    )

    assert highlights.get('acc1|2024-05|grocery') == ['outlier']
    assert 'acc1|2024-01|grocery' not in highlights


def test_compute_highlights_from_transactions_excluded_category():
    """Test that excluded categories are marked 'excluded' and not analyzed."""
    service = StatisticalAnalysisService()
    service.set_user_exclusions('default', ['salary'])
    transactions = [
        _make_transaction('acc1', 'grocery', -100.0),
        _make_transaction('acc1', 'utilities', -50.0),
        _make_transaction('acc1', 'entertainment', -200.0),
        _make_transaction('acc1', 'salary', -500.0),
    ]

    highlights = service.compute_highlights_from_transactions(
        transactions,
        algorithms=['pareto'],
        direction='columns'
    )

    assert highlights.get('acc1|2024-01|salary') == ['excluded']
    # Salary must not take part in the analysis of the other categories
    assert highlights.get('acc1|2024-01|entertainment') == ['pareto']


def test_compute_highlights_from_transactions_filters_income():
    """Test that non-expenses are excluded from analysis by default."""
    service = StatisticalAnalysisService()
    transactions = [
        _make_transaction('acc1', 'grocery', -100.0),
        _make_transaction('acc1', 'utilities', -50.0),
        _make_transaction('acc1', 'entertainment', -200.0),
        _make_transaction('acc1', 'salary', 5000.0),
    ]

    highlights = service.compute_highlights_from_transactions(
        transactions,
        algorithms=['pareto'],
        direction='columns'
    )

    assert 'acc1|2024-01|salary' not in highlights


def test_compute_highlights_from_transactions_separates_accounts():
    """Test that identical categories in different accounts are analyzed independently."""
    service = StatisticalAnalysisService()
    transactions = [
        _make_transaction('acc1', 'grocery', -100.0),
        _make_transaction('acc1', 'utilities', -50.0),
        _make_transaction('acc1', 'entertainment', -200.0),
        _make_transaction('acc2', 'grocery', -300.0),
        _make_transaction('acc2', 'utilities', -50.0),
        _make_transaction('acc2', 'entertainment', -50.0),
    ]

    highlights = service.compute_highlights_from_transactions(
        transactions,
        algorithms=['pareto'],
        direction='columns'
    )

    # Same category names, but each account is analyzed independently:
    # acc1 pareto: entertainment (200), grocery (100); utilities not marked.
    # acc2 pareto: grocery (300), utilities (50); entertainment not marked.
    assert highlights.get('acc1|2024-01|entertainment') == ['pareto']
    assert highlights.get('acc1|2024-01|grocery') == ['pareto']
    assert highlights.get('acc2|2024-01|grocery') == ['pareto']
    assert highlights.get('acc2|2024-01|utilities') == ['pareto']
    assert 'acc2|2024-01|entertainment' not in highlights
    assert 'acc1|2024-01|utilities' not in highlights


def test_compute_highlights_from_transactions_empty_input():
    """Test that empty input returns an empty highlights dict."""
    service = StatisticalAnalysisService()

    highlights = service.compute_highlights_from_transactions(
        [],
        algorithms=['iqr', 'pareto'],
        direction='columns'
    )

    assert highlights == {}


def test_highlight_key_format():
    """Test that highlight keys are formatted correctly."""
    service = StatisticalAnalysisService()

    test_responses = {
        'account1': Account(
            data=[
                AggregatedRow(
                    row_id=str(uuid.uuid4()),
                    category_id='TestCategory',
                    total=DisplayRawField(display='100.00', raw=100.0),
                    date=DateField(display='January 2024', timestamp=1704067200),
                    details=[],
                    is_calculated=False
                )
            ],
            id='account1',
            currency='USD'
        )
    }

    result = service.compute_statistical_metadata(
        account_responses=test_responses,
        algorithms=['iqr'],
        direction=AnalysisDirection.COLUMNS
    )

    # Check that highlights have the correct format
    for highlight in result.highlights:
        assert hasattr(highlight, 'row_id')
        assert hasattr(highlight, 'highlight_types')
        assert highlight.highlight_types[0] in ['outlier', 'pareto', 'excluded']
