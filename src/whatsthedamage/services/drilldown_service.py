"""Drilldown service for handling entity-specific drilldown operations.

This service encapsulates business logic for drilldown operations, following the
service layer pattern established in the whatsthedamage architecture. It provides
a clean interface for controllers to access drilldown functionality while
maintaining separation of concerns.
"""
from typing import Dict, List, Any, Optional
from whatsthedamage.services.interfaces import (
    IIdMappingService, ICacheService,
    IDataFormattingService, IStatisticalAnalysisService
)
from whatsthedamage.models.dt_models import DataTablesResponse, AggregatedRow

class DrilldownService:
    """Service for handling drilldown operations on processing results.

    This service encapsulates the business logic for entity-specific drilldowns,
    providing methods to resolve IDs, retrieve cached data, filter results,
    and build context for template rendering.
    """

    def __init__(
        self,
        id_mapping_service: IIdMappingService,
        cache_service: ICacheService,
        data_formatting_service: IDataFormattingService,
        statistical_analysis_service: IStatisticalAnalysisService
    ):
        """Initialize the drilldown service with required dependencies.

        Args:
            id_mapping_service: Service for mapping between secure IDs and original values
            cache_service: Service for accessing cached processing results
            data_formatting_service: Service for formatting data for presentation
            statistical_analysis_service: Service for statistical analysis operations
        """
        self._id_mapping_service = id_mapping_service
        self._cache_service = cache_service
        self._data_formatting_service = data_formatting_service
        self._statistical_analysis_service = statistical_analysis_service

    def resolve_entity_ids(
        self,
        result_id: str,
        account_id: str,
        entity_id: str,
        entity_type: str
    ) -> Dict[str, Optional[str]]:
        """Resolve secure IDs to original values for drilldown operations.

        Centralizes the ID resolution logic that appears in multiple drilldown handlers.
        Handles both category and month entity types with appropriate error handling.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID
            entity_id: Secure entity ID (category_id or month_id)
            entity_type: Type of entity ('category' or 'month')

        Returns:
            Dict[str, Optional[str]]: Dictionary containing resolved values and filter information
                with keys:
                - 'account_number': original account number
                - 'entity_name': original entity name
                - 'filter_value': value to use for filtering
                - 'error': error message if resolution failed

        """
        resolution: Dict[str, Optional[str]] = {
            'account_number': None,
            'entity_name': None,
            'filter_value': None,
            'error': None
        }

        # Resolve account number
        account_number = self._id_mapping_service.get_account_number(result_id, account_id)
        if not account_number:
            resolution['error'] = 'Invalid account ID (may be due to expired cache)'
            return resolution

        # Resolve entity based on type
        if entity_type == 'category':
            entity_name = self._id_mapping_service.get_category_name(result_id, entity_id)
            filter_value = entity_name
        elif entity_type == 'month':
            entity_name = self._id_mapping_service.get_month_timestamp(entity_id)
            filter_value = entity_name
        else:
            resolution['error'] = 'Invalid entity type'
            return resolution

        if not entity_name:
            resolution['error'] = f'Invalid {entity_type} ID'
            return resolution

        resolution.update({
            'account_number': account_number,
            'entity_name': entity_name,
            'filter_value': filter_value
        })

        return resolution

    def get_cached_data_for_account(self, result_id: str, account_number: Optional[str]) -> Dict[str, Optional[Any]]:
        """Retrieve cached processing result for a specific account.

        Centralizes cache access logic with consistent error handling.
        Follows the pattern established in routes_helpers.get_cached_data_for_drilldown.

        Args:
            result_id: UUID of the cached processing result
            account_number: Original account number

        Returns:
            Dict[str, Optional[Any]]: Dictionary containing:
                - 'dt_response': DataTablesResponse object or None
                - 'error': error message or None if retrieval failed

        """
        result: Dict[str, Optional[Any]] = {
            'dt_response': None,
            'error': None
        }

        if not account_number:
            result['error'] = 'Invalid account number'
            return result

        try:
            cached = self._cache_service.get(result_id)
            if not cached:
                from whatsthedamage.utils.logging import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Cache expiration detected for result_id: {result_id}")
                result['error'] = 'Result not found or cache expired. Please reprocess the file.'
                return result

            dt_response = cached.data.get(account_number)
            if not dt_response:
                result['error'] = f'Account "{account_number}" not found.'
                return result

            result['dt_response'] = dt_response
            return result

        except Exception:
            result['error'] = 'Result not found or expired.'
            return result

    def filter_data_for_entity(
        self,
        dt_response: Optional[DataTablesResponse],
        entity_type: str,
        filter_value: Optional[str]
    ) -> List[AggregatedRow]:
        """Filter drilldown data for a specific entity.

        Applies entity-specific filtering logic to the cached data.
        Supports both category and month filtering patterns.

        Args:
            dt_response: DataTablesResponse containing the data to filter
            entity_type: Type of entity ('category' or 'month')
            filter_value: Value to filter by

        Returns:
            List of filtered AggregatedRow objects

        Example:
            >>> filtered_data = service.filter_data_for_entity(
            >>>     dt_response, 'category', 'Grocery'
            >>> )
        """
        if not dt_response or not filter_value:
            return []

        if entity_type == 'category':
            return [row for row in dt_response.data if row.category == filter_value]
        elif entity_type == 'month':
            return [row for row in dt_response.data if str(row.date.timestamp) == filter_value]
        return []

    def process_statistical_metadata(self, result_id: str) -> Dict[str, List[str]]:
        """Process statistical metadata for template context.

        Encapsulates the statistical metadata processing logic that appears
        in multiple drilldown handlers. Provides consistent error handling.

        Args:
            result_id: UUID of the cached processing result

        Returns:
            Dictionary of highlights for template context, empty dict on error

        Example:
            >>> highlights_dict = service.process_statistical_metadata(result_id)
            >>> # highlights_dict: {'row1': ['outlier'], 'row2': ['pareto']}
        """
        try:
            cached = self._cache_service.get(result_id)
            if cached and cached.statistical_metadata:
                return self._data_formatting_service._convert_metadata_to_highlights_dict(
                    cached.statistical_metadata
                )
        except Exception:
            pass
        return {}

    def build_drilldown_context(
        self,
        filtered_data: List[Any],
        account_number: Optional[str],
        result_id: str,
        account_id: str,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str],
        drilldown_urls: Dict[str, Any],
        template_specific_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build standardized context dictionary for drilldown templates.

        Centralizes context building logic with consistent structure.
        Handles account formatting, statistical metadata, and base context.

        Args:
            filtered_data: Filtered data rows for the template
            account_number: Original account number
            result_id: Processing result ID
            account_id: Secure account ID
            entity_type: Type of entity ('category' or 'month')
            entity_id: Secure entity ID
            entity_name: Original entity name
            drilldown_urls: Pre-generated drilldown URLs
            template_specific_context: Additional context specific to the template

        Returns:
            Complete context dictionary ready for template rendering

        Example:
            >>> context = service.build_drilldown_context(
            >>>     filtered_data, account_number, result_id, account_id,
            >>>     'category', category_id, category_name, drilldown_urls
            >>> )
        """
        if not account_number or not entity_name:
            return {
                'data': filtered_data,
                'account': account_number,
                'formatted_account': None,
                'result_id': result_id,
                'account_id': account_id,
                f'{entity_type}_id': entity_id,
                entity_type: entity_name,
                'urls': drilldown_urls,
                'highlights': {}
            }

        # Format account ID
        formatted_account = self._data_formatting_service.format_account_id(account_number)

        # Process statistical metadata
        highlights_dict = self.process_statistical_metadata(result_id)

        # Build base context
        context = {
            'data': filtered_data,
            'account': account_number,
            'formatted_account': formatted_account,
            'result_id': result_id,
            'account_id': account_id,
            f'{entity_type}_id': entity_id,
            entity_type: entity_name,
            'urls': drilldown_urls,
            'highlights': highlights_dict
        }

        # Add template-specific context if provided
        if template_specific_context:
            context.update(template_specific_context)

        return context

    def generate_drilldown_urls(
        self,
        result_id: str,
        account_number: Optional[str],
        dt_response: Optional[DataTablesResponse]
    ) -> Dict[str, Any]:
        """Generate all drill-down URLs for a result using ID mapping.

        Encapsulates the URL generation logic that involves business rules
        for mapping sensitive data to secure IDs.

        Args:
            result_id: Processing result ID
            account_number: Original account number
            dt_response: DataTablesResponse containing the data

        Returns:
            Dictionary containing pre-generated URLs for all drill-down levels

        Example:
            >>> drilldown_urls = service.generate_drilldown_urls(result_id, account_number, dt_response)
        """
        if not account_number or not dt_response:
            return {
                'account_id': None,
                'category_urls': {},
                'month_urls': {},
                'cell_urls': {}
            }

        # Map account to secure ID
        account_id = self._id_mapping_service.get_account_id(result_id, account_number)

        # Generate category URLs
        category_urls = {}
        for row in dt_response.data:
            category_name = row.category
            if category_name not in category_urls:
                category_id = self._id_mapping_service.get_category_id(result_id, category_name)
                category_urls[category_name] = {
                    'category_url': f"/results/{result_id}/accounts/{account_id}/categories/{category_id}/months",
                    'category_id': category_id
                }

        # Generate month URLs
        month_urls = {}
        for row in dt_response.data:
            month_ts = str(row.date.timestamp)
            if month_ts not in month_urls:
                month_id = self._id_mapping_service.get_month_id(month_ts)
                month_urls[month_ts] = {
                    'month_url': f"/results/{result_id}/accounts/{account_id}/months/{month_id}/categories",
                    'month_id': month_id
                }

        # Generate cell URLs
        cell_urls = {}
        for row in dt_response.data:
            category_name = row.category
            month_ts = str(row.date.timestamp)
            category_id = self._id_mapping_service.get_category_id(result_id, category_name)
            month_id = self._id_mapping_service.get_month_id(month_ts)
            cell_urls[row.row_id] = {
                'cell_url': f"/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions",
                'category_id': category_id,
                'month_id': month_id
            }

        return {
            'account_id': account_id,
            'category_urls': category_urls,
            'month_urls': month_urls,
            'cell_urls': cell_urls
        }
