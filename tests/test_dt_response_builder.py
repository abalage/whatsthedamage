import pytest
from whatsthedamage.models.domain.dt_response_builder import AccountResponseBuilder
from whatsthedamage.models.domain.dt_models import AccountResponse, AggregatedRow, DateField
from whatsthedamage.models.domain.csv_row import CsvRow


@pytest.fixture
def builder():
    """Create a AccountResponseBuilder instance."""
    return AccountResponseBuilder(date_format="%Y-%m-%d")


@pytest.fixture
def mapping():
    """Create attribute mapping for CsvRow."""
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency',
        'category_id': 'category',
        'notice': 'notice',
    }


@pytest.fixture
def sample_csv_rows(mapping):
    """Create sample CSV rows for testing."""
    return [
        CsvRow(
            {"date": "2025-01-15", "amount": "-50.0", "currency": "USD", "partner": "Grocery Store", "type": "purchase"},
            mapping
        ),
        CsvRow(
            {"date": "2025-01-16", "amount": "-30.0", "currency": "USD", "partner": "Gas Station", "type": "purchase"},
            mapping
        ),
        CsvRow(
            {"date": "2025-01-17", "amount": "-25.0", "currency": "USD", "partner": "Coffee Shop", "type": "purchase"},
            mapping
        ),
    ]


def test_builder_initialization(builder):
    """Test that builder initializes correctly."""
    assert builder._date_format == "%Y-%m-%d"
    assert builder._aggregated_rows == []


def test_add_category_data(builder, sample_csv_rows):
    """Test adding category data to the builder."""
    date_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        date_field=date_field
    )

    assert len(builder._aggregated_rows) == 1
    row = builder._aggregated_rows[0]
    assert row.category_id == "grocery"
    assert row.total.raw == pytest.approx(-50.0)
    # Currency comes from row data (USD in sample_csv_rows)
    assert "50.00" in row.total.display
    assert row.date.display == "January"
    assert row.date.timestamp == 1735689600
    assert len(row.details) == 1


def test_add_multiple_categories(builder, sample_csv_rows):
    """Test adding multiple category data entries."""
    date_field = DateField(display="January", timestamp=1735689600)
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        date_field=date_field
    )
    builder.add_category_data(
        category_id="transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        date_field=date_field
    )

    assert len(builder._aggregated_rows) == 2
    assert builder._aggregated_rows[0].category_id == "grocery"
    assert builder._aggregated_rows[1].category_id == "transportation"


def test_build_returns_datatables_response(builder, sample_csv_rows):
    """Test that build() returns a proper AccountResponse."""
    date_field = DateField(display="January", timestamp=1735689600)
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows,
        total_amount=-105.0,
        date_field=date_field
    )

    response = builder.build()

    assert isinstance(response, AccountResponse)
    # Response now includes the original category plus Balance, Total Spendings, and Cost of Living (grocery is in COST_OF_LIVING_CATEGORY_IDS)
    assert len(response.data) == 4
    assert isinstance(response.data[0], AggregatedRow)
    # Verify Balance row is included
    balance_row = next((row for row in response.data if row.category_id == "balance"), None)
    assert balance_row is not None
    # Verify Total Spendings row is included
    spendings_row = next((row for row in response.data if row.category_id == "total_spendings"), None)
    assert spendings_row is not None
    # Verify Cost of Living row is included (grocery is in COST_OF_LIVING_CATEGORY_IDS)
    cost_of_living_row = next((row for row in response.data if row.category_id == "cost_of_living"), None)
    assert cost_of_living_row is not None


def test_build_detail_rows(builder, sample_csv_rows):
    """Test that detail rows are built correctly."""
    details = builder._build_detail_rows(sample_csv_rows)

    assert len(details) == 3
    assert details[0].merchant == "Grocery Store"
    assert details[0].amount.raw == -50.0
    # Currency comes from row data (USD in sample_csv_rows)
    assert "50.00" in details[0].amount.display
    assert details[0].date.display == "2025-01-15"


def test_empty_builder_build(builder):
    """Test building with no data added."""
    response = builder.build()

    assert isinstance(response, AccountResponse)
    assert response.data == []


def test_builder_with_no_currency():
    """Test builder behavior when no currency is provided."""
    builder = AccountResponseBuilder(date_format="%Y-%m-%d")
    mapping = {'date': 'date', 'amount': 'amount', 'currency': 'currency', 'partner': 'partner', 'category_id': 'category'}
    rows = [CsvRow({"date": "2025-01-15", "amount": "50.0", "currency": "", "partner": "Test", "category": ""}, mapping)]
    date_field = DateField(display="January", timestamp=1735689600)

    builder.add_category_data(
        category_id="test",
        rows=rows,
        total_amount=50.0,
        date_field=date_field
    )

    response = builder.build()
    assert response.data[0].total.display == "50.00"  # No currency prefix


def test_date_field_is_preserved(builder, sample_csv_rows):
    """Test that the date_field timestamp is preserved correctly."""
    # Use a specific timestamp for February 2024
    date_field = DateField(display="February", timestamp=1706745600)  # 2024-02-01

    builder.add_category_data(
        category_id="test",
        rows=sample_csv_rows[:1],
        total_amount=-100.0,
        date_field=date_field
    )

    response = builder.build()
    assert response.data[0].date.timestamp == 1706745600
    assert response.data[0].date.display == "February"


def test_balance_category_is_added(builder, sample_csv_rows):
    """Test that Balance category is automatically added with month totals."""
    date_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01

    # Add two categories for the same month (negative amounts = expenses)
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        date_field=date_field
    )
    builder.add_category_data(
        category_id="transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        date_field=date_field
    )

    response = builder.build()

    # Should have 5 rows: Groceries, Transportation, Balance, Total Spendings, and Cost of Living
    assert len(response.data) == 5

    # Find the Balance row
    balance_row = next((row for row in response.data if row.category_id == "balance"), None)
    assert balance_row is not None, "Balance category should be present"

    # Balance should be the sum of all categories (-50.0 + -30.0 = -80.0)
    assert balance_row.total.raw == pytest.approx(-80.0)
    # Currency comes from row data (USD in sample_csv_rows)
    assert "80.00" in balance_row.total.display
    assert balance_row.date.display == "January"
    assert balance_row.date.timestamp == 1735689600
    assert balance_row.details == []  # Balance has no detail rows

    # Find the Total Spendings row
    spendings_row = next((row for row in response.data if row.category_id == "total_spendings"), None)
    assert spendings_row is not None, "Total Spendings category should be present"
    assert spendings_row.total.raw == pytest.approx(80.0)  # Absolute value of expenses
    assert spendings_row.details == []  # Total Spendings has no detail rows

    # Find the Cost of Living row
    cost_of_living_row = next((row for row in response.data if row.category_id == "cost_of_living"), None)
    assert cost_of_living_row is not None, "Cost of Living category should be present"
    # Cost of Living includes both Grocery and Transportation which are in COST_OF_LIVING_CATEGORY_IDS
    assert cost_of_living_row.total.raw == pytest.approx(-80.0)
    assert cost_of_living_row.details == []


def test_balance_multiple_months(builder, sample_csv_rows, mapping):
    """Test that Balance is calculated separately for each month."""
    january_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01
    february_field = DateField(display="February", timestamp=1738368000)  # 2025-02-01

    # January categories (negative amounts = expenses)
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        date_field=january_field
    )
    builder.add_category_data(
        category_id="transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        date_field=january_field
    )

    # February categories
    february_rows = [
        CsvRow(
            {"date": "2025-02-10", "amount": "-40.0", "currency": "USD", "partner": "Grocery Store", "type": "purchase", "category": ""},
            mapping
        ),
    ]
    builder.add_category_data(
        category_id="grocery",
        rows=february_rows,
        total_amount=-40.0,
        date_field=february_field
    )

    response = builder.build()

    # Should have 9 rows: Jan Groceries, Jan Transportation, Feb Groceries, Jan Balance, Feb Balance, Jan Total Spendings, Feb Total Spendings, Jan Cost of Living, Feb Cost of Living
    # Both Grocery and Transportation are in COST_OF_LIVING_CATEGORY_IDS
    assert len(response.data) == 9

    # Find Balance rows
    balance_rows = [row for row in response.data if row.category_id == "balance"]
    assert len(balance_rows) == 2, "Should have Balance for each month"

    # Sort by timestamp
    balance_rows.sort(key=lambda x: x.date.timestamp)

    # January balance: -50.0 + -30.0 = -80.0
    assert balance_rows[0].total.raw == pytest.approx(-80.0)
    assert balance_rows[0].date.display == "January"

    # February balance: -40.0
    assert balance_rows[1].total.raw == pytest.approx(-40.0)
    assert balance_rows[1].date.display == "February"

    # Find Cost of Living rows
    cost_of_living_rows = [row for row in response.data if row.category_id == "cost_of_living"]
    assert len(cost_of_living_rows) == 2, "Should have Cost of Living for both months (Grocery and Transportation match)"
    # Sort by timestamp
    cost_of_living_rows.sort(key=lambda x: x.date.timestamp)
    # January Cost of Living: Grocery (-50) + Transportation (-30) = -80
    assert cost_of_living_rows[0].total.raw == pytest.approx(-80.0)
    # February Cost of Living: Grocery (-40)
    assert cost_of_living_rows[1].total.raw == pytest.approx(-40.0)

def test_balance_with_no_currency(mapping):
    """Test Balance formatting when no currency is provided."""
    builder = AccountResponseBuilder(date_format="%Y-%m-%d")
    rows = [CsvRow({"date": "2025-01-15", "amount": "50.0", "currency": "", "partner": "Test", "category": ""}, mapping)]
    date_field = DateField(display="January", timestamp=1735689600)

    builder.add_category_data(
        category_id="test",
        rows=rows,
        total_amount=50.0,
        date_field=date_field
    )

    response = builder.build()

    # Find Balance row
    balance_row = next((row for row in response.data if row.category_id == "balance"), None)
    assert balance_row is not None
    assert balance_row.total.display == "50.00"  # No currency prefix


def test_calculator_pattern_disable_balance(builder, sample_csv_rows):
    """Test disabling Balance by passing empty calculators list."""
    builder_no_balance = AccountResponseBuilder(
        date_format="%Y-%m-%d",
        calculators=[]  # Explicitly disable all calculators
    )

    date_field = DateField(display="January", timestamp=1735689600)
    builder_no_balance.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        date_field=date_field
    )

def test_build_detail_rows_with_confidence(builder, sample_csv_rows):
    """Test that detail rows include confidence when available."""
    # Add confidence to sample rows
    sample_csv_rows[0].confidence = 0.95
    sample_csv_rows[1].confidence = 0.87
    sample_csv_rows[2].confidence = None  # Test None confidence

    details = builder._build_detail_rows(sample_csv_rows)

    assert len(details) == 3
    assert details[0].confidence == 0.95
    assert details[1].confidence == 0.87
    assert details[2].confidence is None
    assert details[0].merchant == "Grocery Store"
    assert details[0].amount.raw == -50.0

def test_build_detail_rows_without_confidence(builder, sample_csv_rows):
    """Test that detail rows work correctly when confidence is not set."""
    # Ensure no confidence is set
    for row in sample_csv_rows:
        row.confidence = None

    details = builder._build_detail_rows(sample_csv_rows)

    assert len(details) == 3
    assert all(detail.confidence is None for detail in details)
    assert details[0].merchant == "Grocery Store"
    assert details[0].amount.raw == -50.0

def test_full_pipeline_with_confidence(builder, sample_csv_rows):
    """Test the full pipeline including confidence propagation."""
    # Add confidence to sample rows
    sample_csv_rows[0].confidence = 0.95
    sample_csv_rows[1].confidence = 0.87
    sample_csv_rows[2].confidence = 0.92

    date_field = DateField(display="January", timestamp=1735689600)
    builder.add_category_data(
        category_id="grocery",
        rows=sample_csv_rows,
        total_amount=-105.0,
        date_field=date_field
    )

    response = builder.build()

    assert isinstance(response, AccountResponse)
    # Find the Groceries row (not Balance or Total Spendings)
    groceries_row = next((row for row in response.data if row.category_id == "grocery"), None)
    assert groceries_row is not None
    assert len(groceries_row.details) == 3

    # Verify confidence values are preserved
    assert groceries_row.details[0].confidence == 0.95
    assert groceries_row.details[1].confidence == 0.87
    assert groceries_row.details[2].confidence == 0.92
    assert groceries_row.details[0].merchant == "Grocery Store"
    assert groceries_row.details[0].amount.raw == -50.0


def test_build_detail_rows_with_notice(builder, mapping):
    """Test that detail rows include notice when available."""
    rows = [
        CsvRow(
            {"date": "2025-01-15", "amount": "-50.0", "currency": "USD", "partner": "Grocery Store", "type": "purchase", "notice": "Invoice payment", "category": ""},
            mapping
        ),
        CsvRow(
            {"date": "2025-01-16", "amount": "-30.0", "currency": "USD", "partner": "Gas Station", "type": "purchase", "category": ""},
            mapping
        ),
    ]
    details = builder._build_detail_rows(rows)

    assert len(details) == 2
    assert details[0].notice == "Invoice payment"
    assert details[1].notice == ""  # No notice provided, defaults to empty string
    assert details[0].merchant == "Grocery Store"
