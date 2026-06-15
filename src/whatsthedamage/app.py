from flask import Flask
from flask_cors import CORS
import os
from typing import Optional
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.controllers.frontend_routes import frontend_bp
from whatsthedamage.api.error_handlers import register_error_handlers
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.utils.logging import configure_logging, get_logger, LoggerAdapter
from whatsthedamage.services.service_container import ServiceContainer, create_service_container


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
        r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}
    })


def _load_external_config(app: Flask) -> None:
    """Load external configuration file if it exists."""
    config_file = 'config.py'
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)


def _ensure_upload_folder(app: Flask) -> None:
    """Ensure the upload folder exists."""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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

    return service_container


def _register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    app.register_blueprint(main_bp)
    app.register_blueprint(v2_bp)
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