import pytest
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.config.config import AppConfig, CsvConfig, AppContext
from whatsthedamage.config.config import AppArgs
from whatsthedamage.config.config import EnricherPatternSets
from whatsthedamage.models.domain.dt_models import ProcessingResponse
from whatsthedamage.models.api.common import ProcessingMetadata

# Import API fixtures from separate module
pytest_plugins = ['tests.api_fixtures']


# Mock classes for testing routes with ProcessingService
class MockProcessor:
    """Mock processor that provides currency information."""
    def get_currency(self):
        return 'EUR'
    
    def get_currency_from_rows(self, rows):
        """Get currency from rows."""
        return "EUR"


class MockCSVProcessor:
    """Mock CSV processor with nested processor."""
    def __init__(self):
        self.processor = MockProcessor()
    
    def _read_csv_file(self):
        """Mock method to read CSV file and return rows."""
        from whatsthedamage.models.domain.csv_row import CsvRow
        # Return sample rows
        mapping = {
            'date': 'date',
            'type': 'type',
            'partner': 'partner',
            'amount': 'amount',
            'currency': 'currency',
            'category_id': 'category',
            'account': 'account',
        }
        return [
            CsvRow(
                {
                    "date": "2023-01-01",
                    "type": "deposit",
                    "partner": "bank",
                    "amount": "100",
                    "currency": "EUR",
                    "category": ""
                },
                mapping,
            ),
        ]


@pytest.fixture
def mock_processing_service_result():
    """Factory fixture for creating mock ProcessingService results with AccountResponse."""
    from whatsthedamage.models.domain.dt_models import AccountResponse, AggregatedRow, DisplayRawField, DateField, StatisticalMetadata
    import uuid

    def _create_result(data=None):
        if data is None:
            data = {}

        # Create mock AccountResponse
        agg_rows = []
        for category_id, amount in data.items():
            agg_rows.append(
                AggregatedRow(
                    row_id=str(uuid.uuid4()),  # Add required row_id field
                    date=DateField(display="Total", timestamp=0),
                    category_id=category_id,
                    total=DisplayRawField(display=f"{amount:.2f} USD", raw=amount),
                    details=[]
                )
            )

        # Create statistical metadata with empty highlights
        statistical_metadata = StatisticalMetadata(highlights=[])

        dt_response = AccountResponse(
            data=agg_rows,
            currency="USD",
        )

        return ProcessingResponse(
            data= {'default_account': dt_response},
            metadata=ProcessingMetadata(
                row_count=1,
                processing_time=5,
                ml_enabled=True,
                date_range=None
            ),
            result_id=str(uuid.uuid4()),
            statistical_metadata=statistical_metadata,
        )
    return _create_result


@pytest.fixture
def mapping():
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency',
        'category_id': 'category',
        'account': 'account',
        'notice': 'notice',
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

    # Create the AppArgs object
    app_args = AppArgs(
        config="config.yml",
        filename="data.csv",
        category_id="",
        output_format="html",
        nowrap=False,
        verbose=True,
        training_data=False,
        ml=False,
        end_date="2023-12-31",
        filter=None,
        output=None,
        start_date="2023-01-01"
    )

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

@pytest.fixture
def standard_csv_content():
    """Standard CSV content for testing."""
    return """date,amount,currency,partner
2023-01-01,100.00,EUR,Test Grocery
2023-01-02,50.00,EUR,Test Vehicle
"""

@pytest.fixture
def standard_config_content():
    """Standard config content for testing."""
    return """csv:
  dialect: excel
  delimiter: ','
  date_attribute_format: '%Y-%m-%d'
  attribute_mapping:
    date: date
    amount: amount
    currency: currency
    partner: partner
"""

@pytest.fixture
def csv_content(request):
    """Parameterized CSV content fixture.

    Usage:
    @pytest.mark.parametrize('csv_content', ['standard', 'empty', 'large', 'single'], indirect=True)
    def test_with_csv(csv_content):
        # csv_content will be the appropriate CSV string
    """
    content_type = getattr(request, 'param', 'standard')

    if content_type == 'standard':
        return """date,amount,currency,partner
2023-01-01,100.00,EUR,Test Grocery
2023-01-02,50.00,EUR,Test Vehicle
"""
    elif content_type == 'empty':
        return """date,amount,currency,partner
"""
    elif content_type == 'large':
        lines = ["date,amount,currency,partner"]
        for i in range(100):
            lines.append(f"2023-01-{i%28+1:02d},{i*10}.00,EUR,Test Partner {i}")
        return "\n".join(lines)
    elif content_type == 'single':
        return """date,amount,currency,partner
2023-01-01,100.00,EUR,Test Grocery
"""
    else:
        # Default to standard
        return """date,amount,currency,partner
2023-01-01,100.00,EUR,Test Grocery
2023-01-02,50.00,EUR,Test Vehicle
"""

@pytest.fixture
def process_test_data(standard_csv_content, standard_config_content):
    """Helper fixture to prepare test data dictionary for process route tests.

    Args:
        csv_content_override: Optional CSV content override
        config_content_override: Optional config content override
        **extra_data: Additional data fields to include

    Returns:
        Dictionary ready for POST request
    """
    def _prepare_data(csv_content_override=None, config_content_override=None, **extra_data):
        from io import BytesIO

        data = {
            'csrf_token': "test-csrf-token",
            'filename': (BytesIO((csv_content_override or standard_csv_content).encode()), 'test.csv'),
            'config': (BytesIO((config_content_override or standard_config_content).encode()), 'config.yml'),
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
        }
        data.update(extra_data)
        return data
    return _prepare_data


@pytest.fixture
def ml_config():
    """Fixture for MLConfig with default values."""
    from whatsthedamage.config.ml_config import MLConfig
    return MLConfig()


@pytest.fixture
def custom_ml_config():
    """Fixture for MLConfig with custom confidence threshold."""
    from whatsthedamage.config.ml_config import MLConfig
    return MLConfig(ml_confidence_threshold=0.7)
