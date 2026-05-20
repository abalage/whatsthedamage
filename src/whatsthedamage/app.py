from flask import Flask, current_app
from flask_cors import CORS
import os
import gettext
from typing import Optional, Any
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.api.error_handlers import register_error_handlers
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.utils.flask_locale import get_locale
from whatsthedamage.utils.version import get_version
from whatsthedamage.utils.logging import configure_logging, get_logger
from whatsthedamage.services.service_container import ServiceContainer, create_service_container

def create_app(
    config_class: Optional[FlaskAppConfig] = None,
    service_container: Optional[ServiceContainer] = None
) -> Flask:
    # Configure logging before creating Flask app
    # Use INFO level to capture more details, stdout output, and text format for web interface
    configure_logging(log_level="INFO", log_output="stdout", log_format="text")
    logger = get_logger(__name__)
    logger.info("Starting Flask application initialization")

    app: Flask = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # Load default configuration from a class
    app.config.from_object(FlaskAppConfig)

    if config_class:
        app.config.from_object(config_class)

    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}
    })

    logger.info("Flask application configured successfully")

    # Configure Jinja2 environment to make translation functions available to macros
    def jinja_gettext(message: str) -> str:
        """Jinja2 global gettext function that works with macros."""
        lang = get_locale()
        try:
            translations = gettext.translation(
                'messages',  # domain
                localedir=os.path.join(app.root_path, 'locale'),  # adjust if needed
                languages=[lang],
                fallback=True
            )
        except Exception:
            translations = gettext.NullTranslations()
        return translations.gettext(message)

    def jinja_ngettext(singular: str, plural: str, n: int) -> str:
        """Jinja2 global ngettext function that works with macros."""
        lang = get_locale()
        try:
            translations = gettext.translation(
                'messages',  # domain
                localedir=os.path.join(app.root_path, 'locale'),  # adjust if needed
                languages=[lang],
                fallback=True
            )
        except Exception:
            translations = gettext.NullTranslations()
        return translations.ngettext(singular, plural, n)

    # Set up Jinja2 globals for macro access
    app.jinja_env.globals['_'] = jinja_gettext
    app.jinja_env.globals['ngettext'] = jinja_ngettext

    # Check if external config file exists and load it
    config_file = 'config.py'
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize service container
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

    # --- BEGIN: Gettext integration for templates ---
    # Note: File cleanup should be done via background job or event-driven mechanism,
    # not on every request. Consider implementing:
    # - APScheduler for periodic cleanup
    # - Cleanup on upload instead of every request
    # - TTL-based automatic cleanup in upload folder

    @app.context_processor
    def inject_gettext() -> dict[str, Any]:
        # Translation setup moved here to ensure availability during template rendering
        lang = get_locale()
        try:
            translations = gettext.translation(
                'messages',  # domain
                localedir=os.path.join(current_app.root_path, 'locale'),  # adjust if needed
                languages=[lang],
                fallback=True
            )
        except Exception:
            translations = gettext.NullTranslations()

        return {
            '_': translations.gettext,
            'ngettext': translations.ngettext,
            'app_version': get_version(),
            'lang': lang
        }
    # --- END: Gettext integration for templates ---

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(v2_bp)

    # Register error handlers for API routes
    register_error_handlers(app)

    # Add request logging middleware
    @app.before_request
    def log_request_info() -> None:
        """Log basic request information for debugging purposes."""
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

    return app


# Create the app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)