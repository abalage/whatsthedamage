"""Route test factory for creating test clients and setting up test data.

This module provides a factory for creating Flask test clients with properly
configured services and test data for route testing.
"""
from flask import Flask
from typing import Dict, Any
from whatsthedamage.app import create_app
from whatsthedamage.services.response_formatting_service import ResponseFormattingService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.configuration_service import ConfigurationService
from tests.utils.drilldown_test_data_builder import DrilldownTestDataBuilder
from typing import Optional

class RouteTestFactory:
    """Factory for creating test clients and setting up test data for route testing."""

    def create_test_client(self):  # type: ignore[no-untyped-def]
        """Create Flask test client with all services configured.

        Returns:
            Flask test client configured for testing
        """
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        return app.test_client()  # type: ignore[return-value]

    def setup_test_data(
        self,
        result_id: str = 'test123',
        account_number: str = 'ACCT12345678'
    ) -> Dict[str, Any]:
        """Setup cached data and ID mappings for testing.

        Args:
            result_id: ID for the test result
            account_number: Account number to use in test data

        Returns:
            Dictionary containing result_id, account_number, and generated IDs
        """
        # Create test data
        builder = DrilldownTestDataBuilder()
        processing_response = builder.create_processing_response(account_number=account_number)

        # Get services from app context
        from flask import current_app
        cache_service = current_app.extensions['cache_service']
        id_mapping_service = current_app.extensions['id_mapping_service']

        # Setup cache
        cache_service.set(result_id, processing_response)

        # Setup ID mappings
        id_mapping_service.create_mappings_for_result(result_id, processing_response.data)

        # Get generated IDs for use in tests
        account_id = id_mapping_service.get_account_id(result_id, account_number)
        category_ids: Dict[str, Optional[str]] = {}
        month_ids: Dict[str, Optional[str]] = {}

        # Get the DataTablesResponse for the account
        dt_response = processing_response.data.get(account_number)
        if dt_response:
            for row in dt_response.data:
                if row.category not in category_ids:
                    category_ids[row.category] = id_mapping_service.get_category_id(result_id, row.category)
                month_ts = str(row.date.timestamp)
                if month_ts not in month_ids:
                    month_ids[month_ts] = id_mapping_service.get_month_id(month_ts)

        return {
            'result_id': result_id,
            'account_number': account_number,
            'account_id': account_id,
            'category_ids': category_ids,
            'month_ids': month_ids,
            'processing_response': processing_response
        }

    def create_app_with_test_services(self):  # type: ignore[no-untyped-def]
        """Create Flask app with test-configured services.

        Returns:
            Flask app instance with test services
        """
        # Create configuration service
        config_service = ConfigurationService()

        # Create basic Flask app first
        app = create_app()  # type: ignore[assignment]

        # Now create service container with the Flask app and register our test services
        from whatsthedamage.services.service_container import ServiceContainer
        service_container = ServiceContainer(flask_app=app)

        # Override the services we want to test with our specific instances
        service_container._services[ConfigurationService] = config_service
        service_container._services[StatisticalAnalysisService] = StatisticalAnalysisService(
            enabled_algorithms=config_service.get_default_config().enabled_statistical_algorithms
        )
        service_container._services[ResponseFormattingService] = ResponseFormattingService(
            statistical_analysis_service=service_container.get_service(StatisticalAnalysisService)
        )

        # Update Flask extensions with our test services
        app.extensions['configuration_service'] = config_service
        app.extensions['statistical_analysis_service'] = service_container.get_service(StatisticalAnalysisService)
        app.extensions['response_formatting_service'] = service_container.get_service(ResponseFormattingService)

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        return app

    def get_service_from_app(self, app: Flask, service_name: str) -> Any:
        """Get a service from the Flask app extensions.

        Args:
            app: Flask app instance
            service_name: Name of service to retrieve

        Returns:
            The requested service instance
        """
        return app.extensions.get(service_name)