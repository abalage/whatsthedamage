from flask import Flask, g, current_app
import os
import gettext
from flask_caching import Cache
from typing import Optional, Any
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.api.docs import docs_bp
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.api.error_handlers import register_error_handlers
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.utils.flask_locale import get_locale
from whatsthedamage.utils.version import get_version
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.file_upload_service import FileUploadService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.config.dt_models import CachedProcessingResult


class FlaskCacheAdapter:
    """Adapter to make Flask-Caching work with CacheProtocol.

    This adapter allows CacheService to work with Flask-Caching without
    being tightly coupled to it.
    """

    def __init__(self, flask_cache: Cache):
        self._flask_cache = flask_cache

    def set(self, key: str, value: CachedProcessingResult, timeout: int) -> None:
        """Store value in Flask cache."""
        self._flask_cache.set(key, value, timeout=timeout)

    def get(self, key: str) -> Optional[CachedProcessingResult]:
        """Retrieve value from Flask cache."""
        result: Optional[CachedProcessingResult] = self._flask_cache.get(key)
        return result

    def delete(self, key: str) -> None:
        """Remove value from Flask cache."""
        self._flask_cache.delete(key)


def create_app(
    config_class: Optional[FlaskAppConfig] = None,
    processing_service: Optional[ProcessingService] = None,
    validation_service: Optional[ValidationService] = None,
    response_builder_service: Optional[ResponseBuilderService] = None,
    configuration_service: Optional[ConfigurationService] = None,
    file_upload_service: Optional[FileUploadService] = None,
    data_formatting_service: Optional[DataFormattingService] = None,
    statistical_analysis_service: Optional[StatisticalAnalysisService] = None,
    session_service: Optional[SessionService] = None
) -> Flask:
    app: Flask = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # Load default configuration from a class
    app.config.from_object(FlaskAppConfig)

    if config_class:
        app.config.from_object(config_class)

    # Check if external config file exists and load it
    config_file = 'config.py'
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Flask-Caching
    cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

    # Create adapter and cache service (decoupled from Flask-Caching)
    cache_adapter = FlaskCacheAdapter(cache)
    cache_service = CacheService(cache_adapter)
    app.extensions['cache_service'] = cache_service

    # Initialize configuration service first (dependency injection)
    if configuration_service is None:
        configuration_service = ConfigurationService()
    app.extensions['configuration_service'] = configuration_service

    # Initialize statistical analysis service (dependency injection)
    stat_svc = statistical_analysis_service
    if stat_svc is None:
        config = configuration_service.get_default_config()
        # Pass only what's needed: algorithm names list, not entire config
        stat_svc = StatisticalAnalysisService(
            enabled_algorithms=config.enabled_statistical_algorithms
        )
    app.extensions['statistical_analysis_service'] = stat_svc

    # Initialize data formatting service (dependency injection)
    if data_formatting_service is None:
        data_formatting_service = DataFormattingService(statistical_analysis_service=stat_svc)
    app.extensions['data_formatting_service'] = data_formatting_service

    # Initialize processing service (dependency injection)
    if processing_service is None:
        processing_service = ProcessingService(
            configuration_service=configuration_service,
            statistical_analysis_service=stat_svc
        )
    app.extensions['processing_service'] = processing_service

    # Initialize validation service (dependency injection)
    if validation_service is None:
        validation_service = ValidationService()
    app.extensions['validation_service'] = validation_service

    # Initialize file upload service (dependency injection)
    if file_upload_service is None:
        file_upload_service = FileUploadService(validation_service=validation_service)
    app.extensions['file_upload_service'] = file_upload_service

    # Initialize session service (dependency injection)
    if session_service is None:
        session_service = SessionService()
    app.extensions['session_service'] = session_service

    # Initialize response builder service (dependency injection)
    if response_builder_service is None:
        response_builder_service = ResponseBuilderService(formatting_service=data_formatting_service)
    app.extensions['response_builder_service'] = response_builder_service

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
        return dict(_=g._, ngettext=g.ngettext, app_version=get_version())
    # --- END: Gettext integration for templates ---

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(v2_bp)

    # Register error handlers for API routes
    register_error_handlers(app)

    return app


# Create the app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
