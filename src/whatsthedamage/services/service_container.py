"""Unified service container for dependency injection.

This module provides a centralized container for creating service instances
with proper dependency injection that works for both CLI and Web contexts.
"""
from typing import Type, TypeVar, Dict, Any, Optional, cast
from flask import Flask
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.response_formatting_service import ResponseFormattingService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.file_upload_service import FileUploadService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.drilldown_service import DrilldownService
from whatsthedamage.services.drilldown_response_service import DrilldownResponseService
from whatsthedamage.services.ml_service import MLService
from whatsthedamage.services.text_correction_service import TextCorrectionService
from whatsthedamage.services.smote_service import SmoteService
from whatsthedamage.config.config import AppConfig
from flask_caching import Cache

T = TypeVar('T')


class ServiceContainer:
    """Unified container for service instances with dependency injection.

    This class manages service lifecycle and ensures proper dependency
    resolution when creating service instances. It works for both CLI
    and Web contexts.
    """

    def __init__(self, flask_app: Optional[Flask] = None):
        """Initialize service container.

        Args:
            flask_app: Optional Flask app instance for web context
        """
        self._flask_app = flask_app
        self._services: Dict[Type[Any], Any] = {}
        self._config_cache: Optional[AppConfig] = None

    def get_service(self, service_class: Type[T]) -> T:
        """Get a service instance, creating it if necessary.

        Args:
            service_class: Service class to retrieve

        Returns:
            Service instance of the requested type
        """
        if service_class not in self._services:
            self._services[service_class] = self._create_service(service_class)
        return cast(T, self._services[service_class])

    def _create_service(self, service_class: Type[T]) -> T:
        """Create a service instance with proper dependency injection.

        Args:
            service_class: Service class to create

        Returns:
            Newly created service instance

        Raises:
            ValueError: If service_class is not a supported service type or requires Flask context
        """
        # Service creation registry - maps service classes to their creation functions
        service_creators = {
            ConfigurationService: lambda: ConfigurationService(),
            StatisticalAnalysisService: lambda: StatisticalAnalysisService(
                enabled_algorithms=self.get_service(ConfigurationService).get_default_config().enabled_statistical_algorithms
            ),
            ProcessingService: lambda: ProcessingService(
                configuration_service=self.get_service(ConfigurationService),
                statistical_analysis_service=self.get_service(StatisticalAnalysisService)
            ),
            ResponseFormattingService: lambda: ResponseFormattingService(
                statistical_analysis_service=self.get_service(StatisticalAnalysisService)
            ),
            FileUploadService: lambda: FileUploadService(),
            SessionService: lambda: SessionService(),
            MLService: lambda: MLService(),
            TextCorrectionService: lambda: TextCorrectionService(),
            SmoteService: lambda: SmoteService(
                self.get_service(ConfigurationService).get_default_config().ml_config
            ),
        }

        # Web-only services that require Flask app context
        web_service_creators = {
            CacheService: lambda: self._create_cache_service(),
            IdMappingService: lambda: self._create_id_mapping_service(),
            DrilldownService: lambda: self._create_drilldown_service(),
            DrilldownResponseService: lambda: self._create_drilldown_response_service(),
        }

        # Try to create service using appropriate registry
        if service_class in service_creators:
            return service_creators[service_class]()  # type: ignore[no-untyped-call,return-value]
        elif service_class in web_service_creators:
            return web_service_creators[service_class]()  # type: ignore[no-untyped-call,return-value]
        else:
            raise ValueError(f"Unknown service class: {service_class}")

    def _create_cache_service(self) -> CacheService:
        """Create CacheService instance with configured TTL."""
        if self._flask_app is None:
            raise ValueError("CacheService requires Flask app in web context")
        from whatsthedamage.services.cache_service import FlaskCacheAdapter
        cache = Cache(self._flask_app, config={'CACHE_TYPE': 'SimpleCache'})
        adapter = FlaskCacheAdapter(cache)

        # Get cache_ttl from configuration
        config_service = self.get_service(ConfigurationService)
        cache_ttl = config_service.get_default_config().cache_ttl

        return CacheService(adapter, ttl=cache_ttl)

    def _create_id_mapping_service(self) -> IdMappingService:
        """Create IdMappingService instance."""
        if self._flask_app is None:
            raise ValueError("IdMappingService requires Flask app in web context")
        cache_service = self.get_service(CacheService)
        return IdMappingService(cache_service)

    def _create_drilldown_service(self) -> DrilldownService:
        """Create DrilldownService instance."""
        return DrilldownService(
            id_mapping_service=self.get_service(IdMappingService),
            cache_service=self.get_service(CacheService),
            data_formatting_service=self.get_service(ResponseFormattingService),
            statistical_analysis_service=self.get_service(StatisticalAnalysisService)
        )

    def _create_drilldown_response_service(self) -> DrilldownResponseService:
        """Create DrilldownResponseService instance."""
        return DrilldownResponseService(
            id_mapping_service=self.get_service(IdMappingService),
            cache_service=self.get_service(CacheService),
        )

    # Convenience properties for common services
    @property
    def configuration_service(self) -> ConfigurationService:
        """Get ConfigurationService instance."""
        return self.get_service(ConfigurationService)

    @property
    def processing_service(self) -> ProcessingService:
        """Get ProcessingService instance."""
        return self.get_service(ProcessingService)

    @property
    def response_formatting_service(self) -> ResponseFormattingService:
        """Get ResponseFormattingService instance."""
        return self.get_service(ResponseFormattingService)

    @property
    def statistical_analysis_service(self) -> StatisticalAnalysisService:
        """Get StatisticalAnalysisService instance."""
        return self.get_service(StatisticalAnalysisService)

    @property
    def file_upload_service(self) -> FileUploadService:
        """Get FileUploadService instance."""
        return self.get_service(FileUploadService)

    @property
    def session_service(self) -> SessionService:
        """Get SessionService instance."""
        return self.get_service(SessionService)

    @property
    def cache_service(self) -> CacheService:
        """Get CacheService instance (web context only)."""
        return self.get_service(CacheService)

    @property
    def id_mapping_service(self) -> IdMappingService:
        """Get IdMappingService instance (web context only)."""
        return self.get_service(IdMappingService)

    @property
    def drilldown_service(self) -> DrilldownService:
        """Get DrilldownService instance (web context only)."""
        return self.get_service(DrilldownService)

    @property
    def drilldown_response_service(self) -> DrilldownResponseService:
        """Get DrilldownResponseService instance (web context only)."""
        return self.get_service(DrilldownResponseService)

    @property
    def ml_service(self) -> MLService:
        """Get MLService instance."""
        return self.get_service(MLService)

    @property
    def text_correction_service(self) -> TextCorrectionService:
        """Get TextCorrectionService instance."""
        return self.get_service(TextCorrectionService)

    @property
    def smote_service(self) -> SmoteService:
        """Get SmoteService instance."""
        return self.get_service(SmoteService)


def create_service_container(flask_app: Optional[Flask] = None) -> ServiceContainer:
    """Create a new service container.

    Args:
        flask_app: Optional Flask app instance for web context

    Returns:
        Configured service container instance
    """
    return ServiceContainer(flask_app)
