"""Unit tests for DrilldownService.

This module contains comprehensive unit tests for the DrilldownService,
covering all major methods and edge cases.
"""
from tests.utils.drilldown_test_factory import DrilldownTestFactory
from tests.utils.drilldown_test_data_builder import DrilldownTestDataBuilder

class TestDrilldownService:
    """Test suite for DrilldownService."""

    def test_resolve_entity_ids_category_success(self):
        """Test successful category ID resolution."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            id_mappings={
                'account:test123:account1': 'ACCT123',
                'category:test123:cat1': 'Grocery'
            }
        )

        # Execute
        result = service.resolve_entity_ids(
            result_id='test123',
            account_id='account1',
            entity_id='cat1',
            entity_type='category'
        )

        # Verify
        assert result['account_number'] == 'ACCT123'
        assert result['entity_name'] == 'Grocery'
        assert result['filter_value'] == 'Grocery'
        assert result['error'] is None

    def test_resolve_entity_ids_month_success(self):
        """Test successful month ID resolution."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            id_mappings={
                'account:test123:account1': 'ACCT123',
                'month:month1': '1704067200'
            }
        )

        # Execute
        result = service.resolve_entity_ids(
            result_id='test123',
            account_id='account1',
            entity_id='month1',
            entity_type='month'
        )

        # Verify
        assert result['account_number'] == 'ACCT123'
        assert result['entity_name'] == '1704067200'
        assert result['filter_value'] == '1704067200'
        assert result['error'] is None

    def test_resolve_entity_ids_invalid_account(self):
        """Test error handling for invalid account ID."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            id_mappings={
                'account:test123:account1': 'ACCT123'
            }
        )

        # Execute
        result = service.resolve_entity_ids(
            result_id='test123',
            account_id='invalid_account',
            entity_id='cat1',
            entity_type='category'
        )

        # Verify
        assert result['error'] == 'Invalid account ID (may be due to expired cache)'
        assert result['account_number'] is None
        assert result['entity_name'] is None
        assert result['filter_value'] is None

    def test_resolve_entity_ids_invalid_entity_type(self):
        """Test error handling for invalid entity type."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            id_mappings={
                'account:test123:account1': 'ACCT123'
            }
        )

        # Execute
        result = service.resolve_entity_ids(
            result_id='test123',
            account_id='account1',
            entity_id='invalid_id',
            entity_type='invalid_type'
        )

        # Verify
        assert result['error'] == 'Invalid entity type'
        assert result['account_number'] is None  # Should be None when entity type is invalid
        assert result['entity_name'] is None
        assert result['filter_value'] is None

    def test_get_cached_data_for_account_success(self):
        """Test successful cache retrieval."""
        # Setup
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response()
        cache_data = {
            'test123': type('CachedData', (), {
                'data': {'ACCT123': dt_response}
            })()
        }

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(cache_data=cache_data)

        # Execute
        result = service.get_cached_data_for_account('test123', 'ACCT123')

        # Verify
        assert result['dt_response'] == dt_response
        assert result['error'] is None

    def test_get_cached_data_for_account_not_found(self):
        """Test error handling for missing cache data."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(cache_data={})

        # Execute
        result = service.get_cached_data_for_account('test123', 'ACCT123')

        # Verify
        assert result['error'] == 'Result not found or cache expired. Please reprocess the file.'
        assert result['dt_response'] is None

    def test_get_cached_data_for_account_invalid_account(self):
        """Test error handling for invalid account number."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        result = service.get_cached_data_for_account('test123', None)

        # Verify
        assert result['error'] == 'Invalid account number'
        assert result['dt_response'] is None

    def test_filter_data_for_entity_category(self):
        """Test filtering data by category."""
        # Setup
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response(categories=['Grocery', 'Vehicle'])

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        filtered_data = service.filter_data_for_entity(dt_response, 'category', 'Grocery')

        # Verify
        assert len(filtered_data) == 2  # 2 months for Grocery
        assert all(row.category == 'Grocery' for row in filtered_data)

    def test_filter_data_for_entity_month(self):
        """Test filtering data by month."""
        # Setup
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response(months=['1704067200', '1706745600'])

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        filtered_data = service.filter_data_for_entity(dt_response, 'month', '1704067200')

        # Verify
        assert len(filtered_data) == 3  # 3 categories for Jan 2024
        assert all(str(row.date.timestamp) == '1704067200' for row in filtered_data)

    def test_filter_data_for_entity_empty(self):
        """Test filtering with no matching data."""
        # Setup
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response()

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        filtered_data = service.filter_data_for_entity(dt_response, 'category', 'NonExistent')

        # Verify
        assert len(filtered_data) == 0

    def test_process_statistical_metadata_success(self):
        """Test successful statistical metadata processing."""
        # Setup
        builder = DrilldownTestDataBuilder()
        processing_response = builder.create_processing_response()

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            cache_data={'test123': processing_response}
        )

        # Execute
        result = service.process_statistical_metadata('test123')

        # Verify
        assert isinstance(result, dict)
        # The result should be empty dict when no statistical metadata is available
        assert result == {}

    def test_process_statistical_metadata_no_cache(self):
        """Test handling of missing cache data."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        result = service.process_statistical_metadata('nonexistent')

        # Verify
        assert result == {}

    def test_build_drilldown_context_success(self):
        """Test successful context building."""
        # Setup
        builder = DrilldownTestDataBuilder()
        filtered_data = [builder.create_aggregated_row()]

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            formatting_results={
                'account_id': 'ACCT-12345678',
                'highlights': {'row1': ['outlier']}
            }
        )

        # Execute
        context = service.build_drilldown_context(
            filtered_data=filtered_data,
            account_number='ACCT12345678',
            result_id='test123',
            account_id='account1',
            entity_type='category',
            entity_id='cat1',
            entity_name='Grocery',
            drilldown_urls={},
            template_specific_context={'custom': 'value'}
        )

        # Verify
        assert context['data'] == filtered_data
        assert context['account'] == 'ACCT12345678'
        assert context['formatted_account'] == 'ACCT-12345678'
        assert context['result_id'] == 'test123'
        assert context['category_id'] == 'cat1'
        assert context['category'] == 'Grocery'
        assert context['custom'] == 'value'
        assert 'highlights' in context

    def test_build_drilldown_context_missing_account(self):
        """Test context building with missing account number."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        context = service.build_drilldown_context(
            filtered_data=[],
            account_number=None,
            result_id='test123',
            account_id='account1',
            entity_type='category',
            entity_id='cat1',
            entity_name=None,
            drilldown_urls={}
        )

        # Verify
        assert context['account'] is None
        assert context['formatted_account'] is None
        assert context['highlights'] == {}

    def test_generate_drilldown_urls_success(self):
        """Test successful URL generation."""
        # Setup
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response()

        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service(
            id_mappings={
                'account:test123:ACCT12345678': 'account1',
                'account_reverse:test123:ACCT12345678': 'account1',
                'category_reverse:test123:Grocery': 'cat1',
                'month_reverse:1704067200': 'month1'
            }
        )

        # Execute
        urls = service.generate_drilldown_urls('test123', 'ACCT12345678', dt_response)

        # Verify
        assert 'account_id' in urls
        assert 'category_urls' in urls
        assert 'month_urls' in urls
        assert 'cell_urls' in urls
        assert len(urls['category_urls']) == 3  # 3 categories
        assert len(urls['month_urls']) == 2  # 2 months
        assert len(urls['cell_urls']) == 6  # 3 categories × 2 months

    def test_generate_drilldown_urls_missing_data(self):
        """Test URL generation with missing data."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_drilldown_service()

        # Execute
        urls = service.generate_drilldown_urls('test123', None, None)

        # Verify
        assert urls['account_id'] is None
        assert urls['category_urls'] == {}
        assert urls['month_urls'] == {}
        assert urls['cell_urls'] == {}

class TestDrilldownServiceIntegration:
    """Integration tests for DrilldownService with real dependencies."""

    def test_integration_resolve_entity_ids(self):
        """Integration test for entity ID resolution."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_with_real_dependencies()

        # Create test data
        builder = DrilldownTestDataBuilder()
        processing_response = builder.create_processing_response()
        service._cache_service.set('test123', processing_response)

        # Create mappings manually since we're using interface
        from whatsthedamage.services.id_mapping_service import IdMappingService
        id_mapping_service = service._id_mapping_service
        if isinstance(id_mapping_service, IdMappingService):
            id_mapping_service.create_mappings_for_result('test123', processing_response.data)

        # Get the actual generated IDs instead of hardcoded ones
        account_number = 'ACCT12345678'
        category_name = 'Grocery'

        # Get the actual generated IDs
        account_id = id_mapping_service.get_account_id('test123', account_number)
        category_id = id_mapping_service.get_category_id('test123', category_name)

        # Ensure we have valid IDs
        assert account_id is not None, "Account ID should not be None"
        assert category_id is not None, "Category ID should not be None"

        # Execute - use the actual generated IDs
        result = service.resolve_entity_ids(
            result_id='test123',
            account_id=account_id,  # type: ignore[arg-type]
            entity_id=category_id,  # type: ignore[arg-type]
            entity_type='category'
        )

        # Verify
        assert result['account_number'] == account_number
        assert result['entity_name'] == category_name
        assert result['filter_value'] == category_name
        assert result['error'] is None

    def test_integration_get_cached_data(self):
        """Integration test for cached data retrieval."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_with_real_dependencies()

        # Create test data
        builder = DrilldownTestDataBuilder()
        processing_response = builder.create_processing_response()
        service._cache_service.set('test123', processing_response)

        # Execute
        result = service.get_cached_data_for_account('test123', 'ACCT12345678')

        # Verify
        assert result['dt_response'] is not None
        assert len(result['dt_response'].data) == 6  # 3 categories × 2 months
        assert result['error'] is None

    def test_integration_filter_data(self):
        """Integration test for data filtering."""
        # Setup
        factory = DrilldownTestFactory()
        service = factory.create_with_real_dependencies()

        # Create test data
        builder = DrilldownTestDataBuilder()
        dt_response = builder.create_datatables_response()

        # Execute
        filtered_data = service.filter_data_for_entity(dt_response, 'category', 'Grocery')

        # Verify
        assert len(filtered_data) == 2  # 2 months for Grocery
        assert all(row.category == 'Grocery' for row in filtered_data)