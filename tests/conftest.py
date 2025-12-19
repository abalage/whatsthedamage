import os
import pytest
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import AppConfig, CsvConfig, AppContext
from whatsthedamage.config.config import AppArgs
from whatsthedamage.config.config import EnricherPatternSets

# Import API fixtures from separate module
pytest_plugins = ['tests.api_fixtures']


# Centralized config.yml.default path
CONFIG_YML_DEFAULT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../docs/config.yml.default")
)


@pytest.fixture
def config_yml_default_path():
    return CONFIG_YML_DEFAULT_PATH


# Mock classes for testing routes with ProcessingService
class MockProcessor:
    """Mock processor that provides currency information."""
    def get_currency(self):
        return 'EUR'


class MockCSVProcessor:
    """Mock CSV processor with nested processor."""
    def __init__(self):
        self.processor = MockProcessor()


@pytest.fixture
def mock_processing_service_result():
    """Factory fixture for creating mock ProcessingService results."""
    def _create_result(data=None):
        if data is None:
            data = {}
        return {
            'data': data,
            'monthly_data': {'Total': data},  # Mock monthly breakdown
            'metadata': {},
            'processor': MockCSVProcessor()
        }
    return _create_result


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


@pytest.fixture
def client():
    """Flask test client fixture for testing routes and error handlers."""
    from whatsthedamage.app import create_app
    from whatsthedamage.controllers.routes import bp

    config = {
        'TESTING': True,
        'UPLOAD_FOLDER': '/tmp/uploads'
    }
    app = create_app()
    app.config.from_mapping(config)
    app.register_blueprint(bp, name='test_bp')
    with app.test_client() as client:
        with app.app_context():
            yield client
