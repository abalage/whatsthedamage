from flask import Flask
from flask_cors import CORS
import os
from typing import Any, Optional, cast
from sqlalchemy.engine import Engine
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.api.v2.auth.endpoints import auth_bp
from whatsthedamage.controllers.frontend_routes import frontend_bp
from whatsthedamage.api.error_handlers import register_error_handlers
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.config.database_config import DatabaseConfig, Base
from whatsthedamage.config.auth_config import AuthConfig, get_auth_config
from whatsthedamage.utils.logging import configure_logging, get_logger, LoggerAdapter
from whatsthedamage.services.service_container import ServiceContainer, create_service_container
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.session import Session as SessionDB


def _configure_logging() -> None:
    """Configure application logging."""
    configure_logging(log_level="INFO", log_output="stdout", log_format="text")


def _create_flask_app() -> Flask:
    """Create and return a Flask application instance."""
    return Flask(__name__, template_folder='view/templates', static_folder='view/static')


def _configure_flask_app(
    app: Flask,
    config_class: Optional[FlaskAppConfig] = None
) -> None:
    """Load Flask application configuration."""
    app.config.from_object(FlaskAppConfig)
    if config_class:
        app.config.from_object(config_class)


def _configure_cors(app: Flask) -> None:
    """Configure CORS for API endpoints."""
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "supports_credentials": True
        }
    })


def _load_external_config(app: Flask) -> None:
    """Load external configuration file if it exists."""
    config_file = 'config.py'
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)


def _ensure_upload_folder(app: Flask) -> None:
    """Ensure the upload folder exists."""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def _init_database(app: Flask) -> None:
    """Initialize database tables."""
    db_config = DatabaseConfig()
    engine: Engine
    session_factory: Any
    engine, session_factory = db_config.init_db()
    
    # Import models to ensure they're registered with SQLAlchemy metadata
    from whatsthedamage.models.database.user import User as UserDB
    from whatsthedamage.models.database.session import Session as SessionDB
    
    # Create all tables (Users and Sessions only for auth)
    Base.metadata.create_all(engine)
    
    # Store engine in app for later use
    app.extensions['db_engine'] = engine
    app.extensions['db_session_factory'] = session_factory


def _init_auth_services(app: Flask, service_container: ServiceContainer) -> ServiceContainer:
    """Initialize authentication-related services."""
    # Get database session factory
    session_factory = app.extensions.get('db_session_factory')
    if not session_factory:
        _init_database(app)
        session_factory = app.extensions['db_session_factory']
    
    # Create repositories
    from whatsthedamage.models.repositories.user_repository import SqlAlchemyUserRepository
    from whatsthedamage.models.repositories.session_repository import SqlAlchemySessionRepository
    
    user_repo = SqlAlchemyUserRepository(cast(Any, session_factory))
    session_repo = SqlAlchemySessionRepository(cast(Any, session_factory))
    
    # Create auth services
    from whatsthedamage.services.password_service import PasswordService
    from whatsthedamage.services.token_service import TokenService
    from whatsthedamage.services.recovery_code_service import RecoveryCodeService
    from whatsthedamage.services.csrf_service import CsrfService
    from whatsthedamage.services.rate_limit_service import RateLimitService
    from whatsthedamage.services.authentication_service import AuthenticationService
    
    auth_config = get_auth_config()
    
    password_service = PasswordService(
        time_cost=auth_config.PASSWORD_HASH_PARAMETERS['time_cost'],
        memory_cost=auth_config.PASSWORD_HASH_PARAMETERS['memory_cost'],
        parallelism=auth_config.PASSWORD_HASH_PARAMETERS['parallelism'],
        hash_len=auth_config.PASSWORD_HASH_PARAMETERS['hash_len'],
        salt_len=auth_config.PASSWORD_HASH_PARAMETERS['salt_len']
    )
    
    token_service = TokenService(auth_config.SESSION_TOKEN_LENGTH)
    recovery_code_service = RecoveryCodeService(
        code_length=auth_config.RECOVERY_CODE_LENGTH,
        characters=auth_config.RECOVERY_CODE_CHARACTERS
    )
    csrf_service = CsrfService(auth_config.CSRF_TOKEN_LENGTH)
    rate_limit_service = RateLimitService()
    
    auth_service = AuthenticationService(
        user_repository=user_repo,
        session_repository=session_repo,
        password_service=password_service,
        token_service=token_service,
        recovery_code_service=recovery_code_service,
        csrf_service=csrf_service,
        password_min_length=auth_config.PASSWORD_MIN_LENGTH,
        session_timeout=auth_config.PERMANENT_SESSION_LIFETIME,
        remember_me_duration=auth_config.SESSION_REMEMBER_ME_DURATION,
        max_concurrent_sessions=auth_config.SESSION_MAX_CONCURRENT
    )
    
    # Initialize auth endpoints with services
    from whatsthedamage.api.v2.auth.endpoints import init_auth_services
    init_auth_services(auth_service, rate_limit_service)
    
    # Store services in app extensions
    app.extensions['auth_service'] = auth_service
    app.extensions['rate_limit_service'] = rate_limit_service
    app.extensions['password_service'] = password_service
    app.extensions['token_service'] = token_service
    app.extensions['user_repository'] = user_repo
    app.extensions['session_repository'] = session_repo
    
    return service_container


def _initialize_service_container(
    app: Flask,
    service_container: Optional[ServiceContainer] = None
) -> ServiceContainer:
    """Initialize and register the service container."""
    if service_container is None:
        service_container = create_service_container(app)

    # Register services in Flask extensions for backward compatibility
    app.extensions['configuration_service'] = service_container.configuration_service
    app.extensions['processing_service'] = service_container.processing_service
    app.extensions['response_formatting_service'] = service_container.response_formatting_service
    app.extensions['cache_service'] = service_container.cache_service
    app.extensions['id_mapping_service'] = service_container.id_mapping_service
    app.extensions['statistical_analysis_service'] = service_container.statistical_analysis_service
    app.extensions['file_upload_service'] = service_container.file_upload_service
    app.extensions['session_service'] = service_container.session_service
    app.extensions['drilldown_response_service'] = service_container.drilldown_response_service
    
    # Initialize authentication services
    _init_auth_services(app, service_container)

    return service_container


def _register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    app.register_blueprint(main_bp)
    app.register_blueprint(v2_bp)
    # Register auth blueprint
    app.register_blueprint(auth_bp)
    # Register frontend routes LAST so API routes take precedence
    app.register_blueprint(frontend_bp)


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for API routes."""
    register_error_handlers(app)


def _setup_request_logging(app: Flask, logger: LoggerAdapter) -> None:
    """Set up request logging middleware."""
    @app.before_request
    def log_request_info() -> None:
        from flask import request
        if request.path.startswith('/api/'):
            logger.debug(f"API Request: {request.method} {request.path}", extra={
                "context": {
                    "user_agent": request.user_agent.string if request.user_agent else "unknown",
                    "remote_addr": request.remote_addr,
                    "content_type": request.content_type,
                    "content_length": request.content_length
                }
            })


def create_app(
    config_class: Optional[FlaskAppConfig] = None,
    service_container: Optional[ServiceContainer] = None
) -> Flask:
    _configure_logging()
    logger = get_logger(__name__)
    logger.info("Starting Flask application initialization")

    app = _create_flask_app()
    _configure_flask_app(app, config_class)
    _configure_cors(app)

    logger.info("Flask application configured successfully")

    _load_external_config(app)
    _ensure_upload_folder(app)

    service_container = _initialize_service_container(app, service_container)

    _register_blueprints(app)
    _register_error_handlers(app)
    _setup_request_logging(app, logger)

    return app


# Create the app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)