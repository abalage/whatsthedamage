import pytest
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import AppConfig, CsvConfig, AppContext
from whatsthedamage.config.config import AppArgs
from whatsthedamage.config.config import EnricherPatternSets


@pytest.fixture
def mapping():
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency',
        'category': 'category',
    }


@pytest.fixture
def csv_rows(mapping):
    return [
        CsvRow(
            {
                "date": "2023-01-01",
                "type": "deposit",
                "partner": "bank",
                "amount": "100",
                "currency": "EUR"
            },
            mapping,
        ),
        CsvRow(
            {
                "date": "2023-01-02",
                "type": "deposit",
                "partner": "bank",
                "amount": "200",
                "currency": "EUR"
            },
            mapping,
        ),
    ]


@pytest.fixture
def pattern_sets():
    return EnricherPatternSets(
        partner={
            "bank_category": ["bank"],
            "other_category": ["other"]
        },
        type={
            "deposit_category": ["deposit"],
            "withdrawal_category": ["withdrawal"]
        }
    )


@pytest.fixture
def app_context():
    # Create the CsvConfig object
    csv_config = CsvConfig(
        dialect="excel",
        delimiter=",",
        date_attribute_format="%Y-%m-%d",
        attribute_mapping={"date": "date", "amount": "amount"},
    )

    # Create the EnricherPatternSets object
    from whatsthedamage.config.config import EnricherPatternSets
    enricher_pattern_sets = EnricherPatternSets(
        type={"pattern1": ["value1", "value2"], "pattern2": ["value3", "value4"]},
        partner={}
    )

    # Create the AppConfig object
    app_config = AppConfig(
        csv=csv_config,
        enricher_pattern_sets=enricher_pattern_sets
    )

    # Create the AppArgs dictionary
    app_args: AppArgs = {
        "category": "category1",
        "config": "config.yml",
        "filename": "data.csv",
        "no_currency_format": False,
        "nowrap": False,
        "output_format": "html",
        "verbose": True,
        "end_date": "2023-12-31",
        "filter": None,
        "output": None,
        "start_date": "2023-01-01",
        "lang": None,
        "training_data": False,
        "ml": False,
    }

    # Return the AppContext object
    return AppContext(config=app_config, args=app_args)
