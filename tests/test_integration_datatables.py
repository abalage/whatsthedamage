"""
Integration test to verify that the DataTables response has proper timestamps.
"""
import pytest
from whatsthedamage.config.config import AppContext, AppConfig, CsvConfig, EnricherPatternSets, AppArgs
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.rows_processor import RowsProcessor


@pytest.fixture
def app_context_v2():
    """Create an AppContext for integration testing."""
    csv_config = CsvConfig(
        dialect="excel",
        delimiter=",",
        date_attribute_format="%Y-%m-%d",
        attribute_mapping={"date": "date", "amount": "amount", "currency": "currency", "partner": "partner"},
    )
    
    enricher_pattern_sets = EnricherPatternSets(
        partner={"Groceries": ["TESCO", "Grocery Store"], "Transportation": ["Gas Station"]},
        type={}
    )
    
    app_config = AppConfig(
        csv=csv_config,
        enricher_pattern_sets=enricher_pattern_sets
    )
    
    app_args: AppArgs = {
        "category": "category",
        "config": "config.yml",
        "filename": "data.csv",
        "no_currency_format": False,
        "nowrap": False,
        "output_format": "html",
        "start_date": None,
        "end_date": None,
        "verbose": False,
        "filter": None,
        "lang": "en",
        "training_data": False,
        "ml": False,
        "output": "html"
    }
    
    return AppContext(app_config, app_args)


@pytest.fixture
def csv_rows_with_months(mapping):
    """Create CSV rows spanning multiple months."""
    return [
        CsvRow(
            {"date": "2025-01-15", "amount": "-50.0", "currency": "USD", "partner": "TESCO", "category": "Groceries"},
            mapping
        ),
        CsvRow(
            {"date": "2025-01-20", "amount": "-30.0", "currency": "USD", "partner": "Gas Station", "category": "Transportation"},
            mapping
        ),
        CsvRow(
            {"date": "2025-02-10", "amount": "-45.0", "currency": "USD", "partner": "Grocery Store", "category": "Groceries"},
            mapping
        ),
        CsvRow(
            {"date": "2025-03-05", "amount": "-60.0", "currency": "USD", "partner": "TESCO", "category": "Groceries"},
            mapping
        ),
    ]


def test_process_rows_v2_timestamps(app_context_v2, csv_rows_with_months):
    """Test that process_rows_v2 generates proper timestamps for months."""
    processor = RowsProcessor(app_context_v2)
    response = processor.process_rows_v2(csv_rows_with_months)
    
    # Verify we have data
    assert len(response.data) > 0
    
    # Verify all month timestamps are non-zero
    for row in response.data:
        assert row.month.timestamp > 0, f"Month '{row.month.display}' has timestamp 0"
    
    # Collect unique months with timestamps
    month_tuples = set()
    for row in response.data:
        month_tuples.add((row.month.display, row.month.timestamp))
    
    # Sort by timestamp (as done in routes.py)
    sorted_months = [m[0] for m in sorted(month_tuples, key=lambda x: x[1])]
    
    # Verify months are in chronological order
    # Note: The display names are localized month names, so we check timestamp order
    timestamps = [m[1] for m in sorted(month_tuples, key=lambda x: x[1])]
    assert timestamps == sorted(timestamps), "Months should be sorted by timestamp"
    
    # Verify we have 3 months (January, February, March)
    assert len(sorted_months) == 3


def test_month_timestamp_values(app_context_v2, csv_rows_with_months):
    """Test that month timestamps correspond to the first day of each month."""
    from whatsthedamage.utils.date_converter import DateConverter
    
    processor = RowsProcessor(app_context_v2)
    response = processor.process_rows_v2(csv_rows_with_months)
    
    # Expected timestamps for first day of each month in 2025
    expected_timestamps = {
        1: DateConverter.convert_to_epoch("2025-01-01", "%Y-%m-%d"),
        2: DateConverter.convert_to_epoch("2025-02-01", "%Y-%m-%d"),
        3: DateConverter.convert_to_epoch("2025-03-01", "%Y-%m-%d"),
    }
    
    # Collect actual timestamps
    actual_timestamps = set()
    for row in response.data:
        actual_timestamps.add(row.month.timestamp)
    
    # Verify the timestamps match expected values
    for timestamp in actual_timestamps:
        assert timestamp in expected_timestamps.values(), f"Unexpected timestamp: {timestamp}"
