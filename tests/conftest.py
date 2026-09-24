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
    """Factory fixture for creating mock ProcessingService results with Account."""
    from whatsthedamage.models.domain.dt_models import AggregatedRow, DisplayRawField, DateField, StatisticalMetadata
    from whatsthedamage.models.domain.account import Account
    import uuid

    def _create_result(data=None):
        if data is None:
            data = {}

        # Create mock Account
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

        dt_response = Account(
            id="default_account",
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
    from whatsthedamage.config.config import CsvConfig, EnricherPatternSets
    csv_config = CsvConfig(
        dialect="excel",
        delimiter=",",
        date_attribute_format="%Y-%m-%d",
        attribute_mapping={"date": "date", "amount": "amount"},
    )

    # Create the EnricherPatternSets object
    enricher_pattern_sets = EnricherPatternSets(
        type={"pattern1": ["value1", "value2"], "pattern2": ["value3", "value4"]},
        partner={}
    )

    # Create the AppConfig object (without csv field)
    app_config = AppConfig(
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

    # Return the AppContext object with csv_config
    return AppContext(config=app_config, args=app_args, csv_config=csv_config)


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
    return """enricher_pattern_sets:
  type: {}
  partner: {}
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


# Authentication test fixtures

@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database engine for auth testing."""
    from sqlalchemy import create_engine
    from whatsthedamage.models.database.base import Base
    # Import all models to ensure they're registered with SQLAlchemy metadata
    from whatsthedamage.models.database.user import User  # noqa: F401
    from whatsthedamage.models.database.session import Session  # noqa: F401
    from whatsthedamage.models.database.transaction import Transaction  # noqa: F401
    from whatsthedamage.models.database.processing_result import ProcessingResult  # noqa: F401
    from whatsthedamage.models.database.correction import Correction  # noqa: F401
    from whatsthedamage.models.database.shared_correction import SharedCorrection  # noqa: F401
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a database session for auth testing."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def session_factory(db_engine):
    """Create a session factory for repository testing."""
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=db_engine)


@pytest.fixture
def user_repository(session_factory):
    """Create a UserRepository for testing."""
    from whatsthedamage.models.repositories.user_repository import SqlAlchemyUserRepository
    return SqlAlchemyUserRepository(session_factory)


@pytest.fixture
def session_repository(session_factory):
    """Create a SessionRepository for testing."""
    from whatsthedamage.models.repositories.session_repository import SqlAlchemySessionRepository
    return SqlAlchemySessionRepository(session_factory)


@pytest.fixture
def password_service():
    """Create a PasswordService with test-friendly parameters."""
    from whatsthedamage.services.password_service import PasswordService
    return PasswordService(
        time_cost=2,
        memory_cost=16384,
        parallelism=1
    )


@pytest.fixture
def token_service():
    """Create a TokenService for testing."""
    from whatsthedamage.services.token_service import TokenService
    return TokenService(default_length=32)


@pytest.fixture
def recovery_code_service():
    """Create a RecoveryCodeService for testing."""
    from whatsthedamage.services.recovery_code_service import RecoveryCodeService
    return RecoveryCodeService(code_length=16)


@pytest.fixture
def csrf_service():
    """Create a CsrfService for testing."""
    from whatsthedamage.services.csrf_service import CsrfService
    return CsrfService(token_length=32)


@pytest.fixture
def rate_limit_service():
    """Create a RateLimitService for testing."""
    from whatsthedamage.services.rate_limit_service import RateLimitService
    return RateLimitService(max_attempts=5, window_seconds=900)


@pytest.fixture
def auth_service(user_repository, session_repository, password_service, token_service, recovery_code_service, csrf_service):
    """Create an AuthenticationService for testing."""
    from whatsthedamage.services.authentication_service import AuthenticationService
    return AuthenticationService(
        user_repository=user_repository,
        session_repository=session_repository,
        password_service=password_service,
        token_service=token_service,
        recovery_code_service=recovery_code_service,
        csrf_service=csrf_service,
        password_min_length=12,
        session_timeout=3600,
        remember_me_duration=604800,
        max_concurrent_sessions=5
    )
