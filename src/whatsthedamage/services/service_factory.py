"""Service factory for dependency injection.

This module provides a centralized factory for creating service instances
with proper dependency injection for CLI usage only.
"""
from typing import Optional
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService


class ServiceContainer:
    """Container for service instances with dependency injection.

    This class manages service lifecycle and ensures proper dependency
    resolution when creating service instances.
    """

    def __init__(self) -> None:
        """Initialize service container with lazy-loaded services."""
        self._configuration_service: Optional[ConfigurationService] = None
        self._validation_service: Optional[ValidationService] = None
        self._data_formatting_service: Optional[DataFormattingService] = None
        self._processing_service: Optional[ProcessingService] = None
        self._response_builder_service: Optional[ResponseBuilderService] = None
        self._id_mapping_service: Optional[IdMappingService] = None
        self._statistical_analysis_service: Optional[StatisticalAnalysisService] = None

    @property
    def configuration_service(self) -> ConfigurationService:
        """Get or create ConfigurationService instance."""
        if self._configuration_service is None:
            self._configuration_service = ConfigurationService()
        return self._configuration_service

    @property
    def validation_service(self) -> ValidationService:
        """Get or create ValidationService instance."""
        if self._validation_service is None:
            self._validation_service = ValidationService()
        return self._validation_service

    @property
    def data_formatting_service(self) -> DataFormattingService:
        """Get or create DataFormattingService instance."""
        if self._data_formatting_service is None:
            self._data_formatting_service = DataFormattingService()
        return self._data_formatting_service

    @property
    def processing_service(self) -> ProcessingService:
        """Get or create ProcessingService instance with dependencies."""
        if self._processing_service is None:
            self._processing_service = ProcessingService(
                configuration_service=self.configuration_service
            )
        return self._processing_service

    @property
    def response_builder_service(self) -> ResponseBuilderService:
        """Get or create ResponseBuilderService instance with dependencies."""
        if self._response_builder_service is None:
            self._response_builder_service = ResponseBuilderService(
                formatting_service=self.data_formatting_service
            )
        return self._response_builder_service

    @property
    def id_mapping_service(self) -> IdMappingService:
        """Get or create IdMappingService instance.

        Note: In CLI context, this service may have limited functionality
        as it depends on Flask caching. For full functionality, use Flask app.
        """
        if self._id_mapping_service is None:
            # Create a basic IdMappingService for CLI usage
            # This may have limited functionality without Flask cache
            from flask_caching import Cache
            from flask import Flask
            app = Flask(__name__)
            cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
            self._id_mapping_service = IdMappingService(cache)
        return self._id_mapping_service

    @property
    def statistical_analysis_service(self) -> StatisticalAnalysisService:
        """Get or create StatisticalAnalysisService instance."""
        if self._statistical_analysis_service is None:
            # Create statistical analysis service with default configuration
            from whatsthedamage.services.exclusion_service import ExclusionService
            config = self.configuration_service.get_default_config()
            exclusion_service = ExclusionService()
            self._statistical_analysis_service = StatisticalAnalysisService(
                enabled_algorithms=config.enabled_statistical_algorithms,
                exclusion_service=exclusion_service
            )
        return self._statistical_analysis_service


def create_service_container() -> ServiceContainer:
    """Create a new service container with all services.

    This is the main factory function for CLI and standalone usage.

    Returns:
        ServiceContainer: Configured service container instance

    Example:
        >>> container = create_service_container()
        >>> processing_service = container.processing_service
        >>> result = processing_service.process_with_details(...)
    """
    return ServiceContainer()
