import pytest
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import AppConfig, CsvConfig, AppContext
from whatsthedamage.config.config import AppArgs


@pytest.fixture
def mapping():
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency'
    }


@pytest.fixture
def csv_rows(mapping):
    return [
        CsvRow(
            {'date': "2023-01-01", 'type': 'deposit', 'partner': 'bank', 'amount': 100, 'currency': 'EUR'},
            mapping),
        CsvRow(
            {'date': "2023-01-02", 'type': 'deposit', 'partner': 'bank', 'amount': 200, 'currency': 'EUR'},
            mapping),
    ]


@pytest.fixture
def app_context():
    # Create the CsvConfig object
    csv_config = CsvConfig(
        dialect="excel",
        delimiter=",",
        date_attribute_format="%Y-%m-%d",
        attribute_mapping={"date": "date", "amount": "amount"},
    )

    # Define enricher pattern sets
    enricher_pattern_sets = {
        "category1": {
            "pattern1": ["value1", "value2"],
            "pattern2": ["value3", "value4"]
        }
    }

    # Create the AppConfig object
    app_config = AppConfig(
        csv=csv_config,
        enricher_pattern_sets=enricher_pattern_sets
    )

    # Create the AppArgs object
    app_args = AppArgs(
        category="category1",
        config="config.json",
        end_date="2023-12-31",
        filename="data.csv",
        filter="filter_criteria",
        no_currency_format=False,
        nowrap=False,
        output_format="json",
        output=None,
        start_date="2023-01-01",
        verbose=True
    )

    # Return the AppContext object
    return AppContext(config=app_config, args=app_args)
