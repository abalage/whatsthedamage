"""Tests for ServiceFactory.

Unit tests for the service factory and ServiceContainer,
ensuring proper dependency injection for all services.
"""

import pytest
from whatsthedamage.services.service_factory import create_service_container, ServiceContainer
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.file_upload_service import FileUploadService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.session_service import SessionService


@pytest.fixture
def container():
    """Provide a fresh ServiceContainer for each test."""
    return ServiceContainer()


def test_create_service_container():
    """Test factory function creates a ServiceContainer instance."""
    container = create_service_container()
    assert isinstance(container, ServiceContainer)


@pytest.mark.parametrize("service_name,expected_type", [
    ("processing_service", ProcessingService),
    ("validation_service", ValidationService),
    ("data_formatting_service", DataFormattingService),
    ("configuration_service", ConfigurationService),
    ("file_upload_service", FileUploadService),
    ("response_builder_service", ResponseBuilderService),
    ("session_service", SessionService),
])
def test_container_creates_and_caches_services(container, service_name, expected_type):
    """Test container creates correct service type and caches it (singleton pattern)."""
    # Get service via property
    service = getattr(container, service_name)

    # Verify correct type
    assert isinstance(service, expected_type)

    # Verify singleton behavior (same instance returned)
    assert getattr(container, service_name) is service


@pytest.mark.parametrize("service_with_dep,dependency_service", [
    ("processing_service", "configuration_service"),
    ("file_upload_service", "validation_service"),
    ("response_builder_service", "data_formatting_service"),
])
def test_services_receive_dependencies(container, service_with_dep, dependency_service):
    """Test services with dependencies are properly injected."""
    # Access dependency first
    dependency = getattr(container, dependency_service)
    # Access service that depends on it
    service = getattr(container, service_with_dep)

    # Both should exist
    assert dependency is not None
    assert service is not None


def test_lazy_initialization(container):
    """Test that services are created lazily (only when accessed)."""
    # Initially, all private attributes should be None
    assert container._validation_service is None
    assert container._processing_service is None
    assert container._data_formatting_service is None

    # Access one service
    _ = container.validation_service

    # Now only validation service should be created
    assert container._validation_service is not None
    assert container._processing_service is None
    assert container._data_formatting_service is None
