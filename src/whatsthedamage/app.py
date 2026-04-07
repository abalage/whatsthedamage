from flask import Flask, g, current_app
import os
import gettext
from typing import Optional, Any
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.api.docs import docs_bp
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.api.error_handlers import register_error_handlers
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.utils.flask_locale import get_locale
from whatsthedamage.utils.version import get_version
from whatsthedamage.utils.logging import configure_logging, get_logger
from whatsthedamage.services.service_container import ServiceContainer, create_service_container
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.exclusion_service import ExclusionService

def create_app(
    config_class: Optional[FlaskAppConfig] = None,
    service_container: Optional[ServiceContainer] = None
) -> Flask:
    # Configure logging before creating Flask app
    # Use default WARN level, stdout output, and text format for web interface
    configure_logging(log_level="WARN", log_output="stdout", log_format="text")
    logger = get_logger(__name__)
    logger.info("Starting Flask application initialization")

    app: Flask = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # Load default configuration from a class
    app.config.from_object(FlaskAppConfig)

    if config_class:
        app.config.from_object(config_class)

    logger.info("Flask application configured successfully")

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
    app.extensions['validation_service'] = service_container.validation_service
    app.extensions['data_formatting_service'] = service_container.data_formatting_service
    app.extensions['processing_service'] = service_container.processing_service
    app.extensions['response_builder_service'] = service_container.response_builder_service
    app.extensions['cache_service'] = service_container.cache_service
    app.extensions['id_mapping_service'] = service_container.id_mapping_service
    app.extensions['exclusion_service'] = service_container.get_service(ExclusionService)
    app.extensions['statistical_analysis_service'] = service_container.statistical_analysis_service
    app.extensions['file_upload_service'] = service_container.file_upload_service
    app.extensions['session_service'] = service_container.session_service
    app.extensions['drilldown_service'] = service_container.drilldown_service

    # --- BEGIN: Gettext integration for templates ---
    # Note: File cleanup should be done via background job or event-driven mechanism,
    # not on every request. Consider implementing:
    # - APScheduler for periodic cleanup
    # - Cleanup on upload instead of every request
    # - TTL-based automatic cleanup in upload folder

    @app.before_request
    def set_gettext() -> None:
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
        g._ = translations.gettext
        g.ngettext = translations.ngettext
        # Store language in g for templates if needed
        g.lang = lang

    @app.context_processor
    def inject_gettext() -> dict[str, Any]:
        return {'_': g._, 'ngettext': g.ngettext, 'app_version': get_version()}
    # --- END: Gettext integration for templates ---

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(v2_bp)

    # Register error handlers for API routes
    register_error_handlers(app)

    return app

def _get_id_mapping_service() -> IdMappingService:
    """Get ID mapping service from app extensions (dependency injection)."""
    from typing import cast
    return cast(IdMappingService, current_app.extensions['id_mapping_service'])

# Create the app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)