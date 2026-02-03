"""Integration test for excluded cells highlighting feature.

This test verifies the complete pipeline from DataTablesResponse
through statistical analysis to template data preparation.
"""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.exclusion_service import ExclusionService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField, DetailRow
import uuid

@pytest.fixture
def complete_dt_response():
    """Create a complete DataTablesResponse with various row types."""
    # Create detail rows for regular transactions
    details_grocery = [
        DetailRow(
            row_id=str(uuid.uuid4()),
            date=DateField(display="2023-01-15", timestamp=1673779200),
            amount=DisplayRawField(display="100.00", raw=100.0),
            merchant="Supermarket",
            currency="EUR",
            account="12345678"
        )
    ]

    details_rent = [
        DetailRow(
            row_id=str(uuid.uuid4()),
            date=DateField(display="2023-01-10", timestamp=1673347200),
            amount=DisplayRawField(display="500.00", raw=500.0),
            merchant="Landlord Inc",
            currency="EUR",
            account="12345678"
        )
    ]

    details_utilities = [
        DetailRow(
            row_id=str(uuid.uuid4()),
            date=DateField(display="2023-02-15", timestamp=1676361600),
            amount=DisplayRawField(display="200.00", raw=200.0),
            merchant="Electric Co",
            currency="EUR",
            account="12345678"
        )
    ]

    # Create regular transaction rows
    regular_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details_grocery,
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Rent",
            total=DisplayRawField(display="500.00", raw=500.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=details_rent,
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Utilities",
            total=DisplayRawField(display="200.00", raw=200.0),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=details_utilities,
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Dining",
            total=DisplayRawField(display="150.00", raw=150.0),
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
            total=DisplayRawField(display="850.00", raw=850.0),
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

def test_end_to_end_excluded_highlights_pipeline(complete_dt_response):
    """Test the complete pipeline from DataTablesResponse to template data."""
    # Step 1: Create exclusion service with some excluded categories
    exclusion_service = ExclusionService()
    exclusion_service.set_user_exclusions("default", ["Rent", "Deposit"])

    # Step 2: Create statistical analysis service
    statistical_service = StatisticalAnalysisService(
        enabled_algorithms=["iqr", "pareto"],
        exclusion_service=exclusion_service
    )

    # Step 3: Compute statistical metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": complete_dt_response
    })

    # Verify metadata has highlights
    assert metadata is not None
    assert len(metadata.highlights) > 0

    # Step 4: Attach metadata to the DataTablesResponse
    complete_dt_response.statistical_metadata = metadata

    # Step 5: Create data formatting service
    formatting_service = DataFormattingService(statistical_analysis_service=statistical_service)

    # Step 6: Prepare data for template
    template_data = formatting_service.prepare_accounts_for_template({
        "account1": complete_dt_response
    })

    # Verify template data structure
    assert "accounts" in template_data
    assert len(template_data["accounts"]) == 1
    assert "has_multiple_accounts" in template_data

    account_data = template_data["accounts"][0]
    assert "highlights" in account_data
    assert isinstance(account_data["highlights"], dict)

    # Verify highlights dictionary contains excluded highlights
    excluded_highlights = {
        key: value for key, value in account_data["highlights"].items()
        if value == "excluded"
    }

    # Should have excluded highlights for:
    # 1. Calculated rows (Balance, Total)
    # 2. Excluded categories (Rent)
    assert len(excluded_highlights) > 0

def test_template_highlight_application():
    """Test that highlights can be applied to template data correctly."""
    # Create a mock DataTablesResponse with calculated rows
    calculated_row = AggregatedRow(
        row_id=str(uuid.uuid4()),
        category="Balance",
        total=DisplayRawField(display="100.00", raw=100.0),
        date=DateField(display="January 2023", timestamp=1672531200),
        details=[],
        is_calculated=True
    )

    dt_response = DataTablesResponse(
        data=[calculated_row],
        account="12345678",
        currency="EUR"
    )

    # Create services
    exclusion_service = ExclusionService()
    statistical_service = StatisticalAnalysisService(
        exclusion_service=exclusion_service
    )
    formatting_service = DataFormattingService(
        statistical_analysis_service=statistical_service
    )

    # Compute metadata
    metadata = statistical_service.compute_statistical_metadata({
        "account1": dt_response
    })

    # Attach metadata to the DataTablesResponse
    dt_response.statistical_metadata = metadata

    # Prepare template data
    template_data = formatting_service.prepare_accounts_for_template({
        "account1": dt_response
    })

    # Verify the calculated row is marked as excluded
    account_data = template_data["accounts"][0]
    highlights = account_data["highlights"]

    # The calculated row should have an excluded highlight
    balance_key = calculated_row.row_id
    assert balance_key in highlights
    assert highlights[balance_key] == "excluded"
