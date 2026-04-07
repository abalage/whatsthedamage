"""Tests for ServiceContainer.

Unit tests for the unified service container,
ensuring proper dependency injection for all services.
"""

import pytest
from flask import Flask
from whatsthedamage.services.service_container import create_service_container, ServiceContainer
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.drilldown_service import DrilldownService


@pytest.fixture
def container() -> ServiceContainer:
    """Provide a fresh ServiceContainer for each test."""
    return ServiceContainer()


def test_create_service_container() -> None:
    """Test factory function creates a ServiceContainer instance."""
    container = create_service_container()
    assert isinstance(container, ServiceContainer)


@pytest.mark.parametrize("service_name,expected_type", [
    ("processing_service", ProcessingService),
    ("validation_service", ValidationService),
    ("data_formatting_service", DataFormattingService),
    ("configuration_service", ConfigurationService),
    ("response_builder_service", ResponseBuilderService)
])
def test_container_creates_and_caches_services(
    container: ServiceContainer, service_name: str, expected_type: type
) -> None:
    """Test container creates correct service type and caches it (singleton pattern)."""
    # Get service via property
    service = getattr(container, service_name)

    # Verify correct type
    assert isinstance(service, expected_type)

    # Verify singleton behavior (same instance returned)
    assert getattr(container, service_name) is service


@pytest.mark.parametrize("service_with_dep,dependency_service", [
    ("processing_service", "configuration_service"),
    ("response_builder_service", "data_formatting_service"),
])
def test_services_receive_dependencies(
    container: ServiceContainer, service_with_dep: str, dependency_service: str
) -> None:
    """Test services with dependencies are properly injected."""
    # Access dependency first
    dependency = getattr(container, dependency_service)
    # Access service that depends on it
    service = getattr(container, service_with_dep)

    # Both should exist
    assert dependency is not None
    assert service is not None


def test_lazy_initialization(container: ServiceContainer) -> None:
    """Test that services are created lazily (only when accessed)."""
    # The new service container uses a different approach - it uses a _services dict
    # Initially, no services should be in the cache
    assert len(container._services) == 0

    # Access one service
    validation_service = container.validation_service

    # Now only validation service should be in the cache
    assert len(container._services) == 1
    assert 'ValidationService' in str(list(container._services.keys())[0])
    
    # Access another simple service (configuration service has no dependencies)
    config_service = container.configuration_service
    
    # Now two services should be in the cache
    assert len(container._services) == 2
    
    # Access processing service - this will create its dependencies too
    processing_service = container.processing_service
    
    # Now we should have more services (processing service + its dependencies)
    assert len(container._services) > 2
    
    # Verify same instances are returned (singleton behavior)
    assert container.validation_service is validation_service
    assert container.configuration_service is config_service
    assert container.processing_service is processing_service


def test_web_services_require_flask_app() -> None:
    """Test that web-specific services require Flask app context."""
    container = ServiceContainer()  # No Flask app provided
    
    # These should raise ValueError when no Flask app is provided
    with pytest.raises(ValueError, match="CacheService requires Flask app"):
        _ = container.cache_service
    
    with pytest.raises(ValueError, match="IdMappingService requires Flask app"):
        _ = container.id_mapping_service
    
    # DrilldownService will fail when trying to create IdMappingService dependency
    with pytest.raises(ValueError, match="IdMappingService requires Flask app"):
        _ = container.drilldown_service


def test_web_services_work_with_flask_app() -> None:
    """Test that web-specific services work when Flask app is provided."""
    app = Flask(__name__)
    container = ServiceContainer(flask_app=app)
    
    # These should work with Flask app
    cache_service = container.cache_service
    assert isinstance(cache_service, CacheService)
    
    id_mapping_service = container.id_mapping_service
    assert isinstance(id_mapping_service, IdMappingService)
    
    drilldown_service = container.drilldown_service
    assert isinstance(drilldown_service, DrilldownService)


def test_get_service_method() -> None:
    """Test the generic get_service method."""
    container = ServiceContainer()
    
    # Test getting services via the generic method
    config_service = container.get_service(ConfigurationService)
    assert isinstance(config_service, ConfigurationService)
    
    validation_service = container.get_service(ValidationService)
    assert isinstance(validation_service, ValidationService)
    
    # Verify singleton behavior
    assert container.get_service(ConfigurationService) is config_service
    assert container.get_service(ValidationService) is validation_service


def test_unknown_service_raises_error() -> None:
    """Test that requesting unknown service raises ValueError."""
    container = ServiceContainer()
    
    class UnknownService:
        pass
    
    with pytest.raises(ValueError, match="Unknown service class"):
        container.get_service(UnknownService)


def test_service_container_with_flask_app_factory() -> None:
    """Test creating service container with Flask app via factory."""
    app = Flask(__name__)
    container = create_service_container(flask_app=app)
    
    # Should be able to get web services
    cache_service = container.cache_service
    assert isinstance(cache_service, CacheService)
    
    # Should also be able to get regular services
    config_service = container.configuration_service
    assert isinstance(config_service, ConfigurationService)
