import pytest
from whatsthedamage.models.dt_response_builder import DataTablesResponseBuilder
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DateField
from whatsthedamage.models.csv_row import CsvRow


@pytest.fixture
def builder():
    """Create a DataTablesResponseBuilder instance."""
    return DataTablesResponseBuilder(currency="USD", date_format="%Y-%m-%d")


@pytest.fixture
def mapping():
    """Create attribute mapping for CsvRow."""
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency',
        'category': 'category',
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
    assert builder._currency == "USD"
    assert builder._date_format == "%Y-%m-%d"
    assert builder._aggregated_rows == []


def test_add_category_data(builder, sample_csv_rows):
    """Test adding category data to the builder."""
    month_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01
    builder.add_category_data(
        category="Groceries",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        month_field=month_field
    )
    
    assert len(builder._aggregated_rows) == 1
    row = builder._aggregated_rows[0]
    assert row.category == "Groceries"
    assert row.total.raw == pytest.approx(-50.0)
    assert row.total.display == "USD -50.00"
    assert row.month.display == "January"
    assert row.month.timestamp == 1735689600
    assert len(row.details) == 1


def test_add_multiple_categories(builder, sample_csv_rows):
    """Test adding multiple category data entries."""
    month_field = DateField(display="January", timestamp=1735689600)
    builder.add_category_data(
        category="Groceries",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        month_field=month_field
    )
    builder.add_category_data(
        category="Transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        month_field=month_field
    )
    
    assert len(builder._aggregated_rows) == 2
    assert builder._aggregated_rows[0].category == "Groceries"
    assert builder._aggregated_rows[1].category == "Transportation"


def test_build_returns_datatables_response(builder, sample_csv_rows):
    """Test that build() returns a proper DataTablesResponse."""
    month_field = DateField(display="January", timestamp=1735689600)
    builder.add_category_data(
        category="Groceries",
        rows=sample_csv_rows,
        total_amount=-105.0,
        month_field=month_field
    )
    
    response = builder.build()
    
    assert isinstance(response, DataTablesResponse)
    # Response now includes the original category plus Balance and Total Spendings
    assert len(response.data) == 3
    assert isinstance(response.data[0], AggregatedRow)
    # Verify Balance row is included
    balance_row = next((row for row in response.data if row.category == "Balance"), None)
    assert balance_row is not None
    # Verify Total Spendings row is included
    spendings_row = next((row for row in response.data if row.category == "Total Spendings"), None)
    assert spendings_row is not None


def test_build_detail_rows(builder, sample_csv_rows):
    """Test that detail rows are built correctly."""
    details = builder._build_detail_rows(sample_csv_rows)

    assert len(details) == 3
    assert details[0].merchant == "Grocery Store"
    assert details[0].amount.raw == -50.0
    assert details[0].amount.display == "USD -50.00"
    assert details[0].date.display == "2025-01-15"


def test_empty_builder_build(builder):
    """Test building with no data added."""
    response = builder.build()
    
    assert isinstance(response, DataTablesResponse)
    assert response.data == []


def test_builder_with_no_currency():
    """Test builder behavior when no currency is provided."""
    builder = DataTablesResponseBuilder(currency="", date_format="%Y-%m-%d")
    mapping = {'date': 'date', 'amount': 'amount', 'currency': 'currency', 'partner': 'partner'}
    rows = [CsvRow({"date": "2025-01-15", "amount": "50.0", "currency": "", "partner": "Test"}, mapping)]
    month_field = DateField(display="January", timestamp=1735689600)
    
    builder.add_category_data(
        category="Test",
        rows=rows,
        total_amount=50.0,
        month_field=month_field
    )
    
    response = builder.build()
    assert response.data[0].total.display == "50.00"  # No currency prefix


def test_month_field_is_preserved(builder, sample_csv_rows):
    """Test that the month_field timestamp is preserved correctly."""
    # Use a specific timestamp for February 2024
    month_field = DateField(display="February", timestamp=1706745600)  # 2024-02-01
    
    builder.add_category_data(
        category="Test",
        rows=sample_csv_rows[:1],
        total_amount=-100.0,
        month_field=month_field
    )
    
    response = builder.build()
    assert response.data[0].month.timestamp == 1706745600
    assert response.data[0].month.display == "February"


def test_balance_category_is_added(builder, sample_csv_rows):
    """Test that Balance category is automatically added with month totals."""
    month_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01
    
    # Add two categories for the same month (negative amounts = expenses)
    builder.add_category_data(
        category="Groceries",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        month_field=month_field
    )
    builder.add_category_data(
        category="Transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        month_field=month_field
    )
    
    response = builder.build()
    
    # Should have 4 rows: Groceries, Transportation, Balance, and Total Spendings
    assert len(response.data) == 4
    
    # Find the Balance row
    balance_row = next((row for row in response.data if row.category == "Balance"), None)
    assert balance_row is not None, "Balance category should be present"
    
    # Balance should be the sum of all categories (-50.0 + -30.0 = -80.0)
    assert balance_row.total.raw == pytest.approx(-80.0)
    assert balance_row.total.display == "USD -80.00"
    assert balance_row.month.display == "January"
    assert balance_row.month.timestamp == 1735689600
    assert balance_row.details == []  # Balance has no detail rows
    
    # Find the Total Spendings row
    spendings_row = next((row for row in response.data if row.category == "Total Spendings"), None)
    assert spendings_row is not None, "Total Spendings category should be present"
    assert spendings_row.total.raw == pytest.approx(80.0)  # Absolute value of expenses
    assert spendings_row.details == []  # Total Spendings has no detail rows


def test_balance_multiple_months(builder, sample_csv_rows, mapping):
    """Test that Balance is calculated separately for each month."""
    january_field = DateField(display="January", timestamp=1735689600)  # 2025-01-01
    february_field = DateField(display="February", timestamp=1738368000)  # 2025-02-01
    
    # January categories (negative amounts = expenses)
    builder.add_category_data(
        category="Groceries",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        month_field=january_field
    )
    builder.add_category_data(
        category="Transportation",
        rows=sample_csv_rows[1:2],
        total_amount=-30.0,
        month_field=january_field
    )
    
    # February categories
    february_rows = [
        CsvRow(
            {"date": "2025-02-10", "amount": "-40.0", "currency": "USD", "partner": "Grocery Store", "type": "purchase"},
            mapping
        ),
    ]
    builder.add_category_data(
        category="Groceries",
        rows=february_rows,
        total_amount=-40.0,
        month_field=february_field
    )
    
    response = builder.build()
    
    # Should have 7 rows: Jan Groceries, Jan Transportation, Feb Groceries, Jan Balance, Feb Balance, Jan Total Spendings, Feb Total Spendings
    assert len(response.data) == 7
    
    # Find Balance rows
    balance_rows = [row for row in response.data if row.category == "Balance"]
    assert len(balance_rows) == 2, "Should have Balance for each month"
    
    # Sort by timestamp
    balance_rows.sort(key=lambda x: x.month.timestamp)
    
    # January balance: -50.0 + -30.0 = -80.0
    assert balance_rows[0].total.raw == pytest.approx(-80.0)
    assert balance_rows[0].month.display == "January"
    
    # February balance: -40.0
    assert balance_rows[1].total.raw == pytest.approx(-40.0)
    assert balance_rows[1].month.display == "February"


def test_balance_with_no_currency(mapping):
    """Test Balance formatting when no currency is provided."""
    builder = DataTablesResponseBuilder(currency="", date_format="%Y-%m-%d")
    rows = [CsvRow({"date": "2025-01-15", "amount": "50.0", "currency": "", "partner": "Test"}, mapping)]
    month_field = DateField(display="January", timestamp=1735689600)
    
    builder.add_category_data(
        category="Test",
        rows=rows,
        total_amount=50.0,
        month_field=month_field
    )
    
    response = builder.build()
    
    # Find Balance row
    balance_row = next((row for row in response.data if row.category == "Balance"), None)
    assert balance_row is not None
    assert balance_row.total.display == "50.00"  # No currency prefix


def test_calculator_pattern_disable_balance(builder, sample_csv_rows):
    """Test disabling Balance by passing empty calculators list."""
    builder_no_balance = DataTablesResponseBuilder(
        currency="USD",
        date_format="%Y-%m-%d",
        calculators=[]  # Explicitly disable all calculators
    )

    month_field = DateField(display="January", timestamp=1735689600)
    builder_no_balance.add_category_data(
        category="Groceries",
        rows=sample_csv_rows[:1],
        total_amount=-50.0,
        month_field=month_field
    )
