"""Drilldown Response Service for building consistent drilldown API responses.

This service encapsulates the business logic for building drilldown responses
(get_category_months, get_month_categories, category_month_transactions)
with consistent highlight handling.
It follows the established service layer pattern and uses dependency injection.

Architecture Patterns:
- Service Layer: Business logic isolated from controllers
- Dependency Injection: Services injected via constructor
- Single Responsibility: Each method handles one specific drilldown type
- DRY: Common highlight aggregation logic centralized
"""
import datetime
from typing import Any, Dict, List, Optional
from whatsthedamage.models.dt_models import ProcessingResponse, AggregatedRow
from whatsthedamage.services.interfaces import (
    IIdMappingService,
    ICacheService,
)


class DrilldownResponseService:
    """Service for building drilldown responses with consistent highlight handling.

    This service provides methods to build responses for drilldown endpoints
    (category months, month categories) while maintaining consistency with
    the highlights computed during the original processing via process_transactions.

    The key principle: drilldown endpoints do NOT recalculate highlights.
    Instead, they filter and aggregate the existing highlights from the
    parent ProcessingResponse's statistical_metadata.
    """

    def __init__(
        self,
        id_mapping_service: IIdMappingService,
        cache_service: ICacheService,
    ):
        """Initialize the drilldown response service.

        Args:
            id_mapping_service: Service for mapping between secure IDs and original values
            cache_service: Service for accessing cached processing results
        """
        self._id_mapping_service = id_mapping_service
        self._cache_service = cache_service

    def get_category_months_response(
        self,
        result_id: str,
        account_id: str,
        category_id: str,
    ) -> Dict[str, Any]:
        """Build response for category months drilldown endpoint.

        Retrieves cached processing result, filters by account and category,
        groups transactions by month, aggregates totals, and aggregates highlights
        from the original processing result.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to get months for

        Returns:
            Dictionary with structure:
            - result_id: Processing result ID
            - account_id: Account ID
            - account_name: Account name
            - category_id: Category ID
            - category_name: Resolved category name
            - data: List of month entries with totals and URLs
            - highlights: Aggregated highlights for drilldown rows

        Raises:
            ValueError: If result, account, or category not found
        """
        # Get cached result
        cached_result = self._cache_service.get(result_id)
        if not cached_result:
            raise ValueError('Results not found')

        # Find account data
        account_data = self._find_account_data(cached_result, account_id, result_id)
        if not account_data:
            raise ValueError('Account not found in results')

        # Resolve category ID to original name
        original_category = self._id_mapping_service.get_category_name(result_id, category_id)
        if not original_category:
            original_category = category_id

        # Filter rows by category and group by month
        category_rows = self._filter_rows_by_category(account_data['data'], original_category)

        month_groups = self._group_rows_by_month(category_rows)

        if not month_groups:
            raise ValueError('Category not found or has no data')

        # Build response data
        months_list = self._build_months_list(
            month_groups, result_id, account_id, category_id, original_category
        )

        # Get category display name
        category_name = self._get_category_display_name(account_data['data'], original_category)

        response_data: Dict[str, Any] = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'category_id': category_id,
            'category_name': category_name,
            'data': months_list,
        }

        # Aggregate highlights for drilldown rows
        highlights = self._aggregate_highlights_for_drilldown(
            cached_result, month_groups, original_category
        )
        if highlights:
            response_data['highlights'] = highlights

        return response_data

    def get_month_categories_response(
        self,
        result_id: str,
        account_id: str,
        month_id: str,
    ) -> Dict[str, Any]:
        """Build response for month categories drilldown endpoint.

        Retrieves cached processing result, filters by account and month,
        groups transactions by category, aggregates totals, and aggregates highlights
        from the original processing result.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            month_id: Secure month ID to get categories for

        Returns:
            Dictionary with structure:
            - result_id: Processing result ID
            - account_id: Account ID
            - account_name: Account name
            - month_id: Month ID
            - month_name: Resolved month name
            - data: List of category entries with totals and URLs
            - highlights: Aggregated highlights for drilldown rows

        Raises:
            ValueError: If result, account, or month not found
        """
        # Get cached result
        cached_result = self._cache_service.get(result_id)
        if not cached_result:
            raise ValueError('Results not found')

        # Find account data
        account_data = self._find_account_data(cached_result, account_id, result_id)
        if not account_data:
            raise ValueError('Account not found in results')

        # Resolve month ID to original timestamp
        original_month_ts = self._id_mapping_service.get_month_timestamp(month_id)
        if not original_month_ts:
            original_month_ts = month_id

        # Filter rows by month and group by category
        month_rows = self._filter_rows_by_month(account_data['data'], original_month_ts)

        category_groups = self._group_rows_by_category(month_rows)

        if not category_groups:
            raise ValueError('Month not found or has no data')

        # Build response data
        categories_list = self._build_categories_list(
            category_groups, result_id, account_id, month_id, original_month_ts
        )

        # Get month display name
        month_name = self._get_month_display_name(account_data['data'], original_month_ts)

        response_data: Dict[str, Any] = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'month_id': month_id,
            'month_name': month_name,
            'data': categories_list,
        }

        # Aggregate highlights for drilldown rows
        highlights = self._aggregate_highlights_for_drilldown(
            cached_result, category_groups, None, original_month_ts
        )
        if highlights:
            response_data['highlights'] = highlights

        return response_data

    def _find_account_data(
        self,
        cached_result: ProcessingResponse,
        account_id: str,
        result_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find account data in cached result by account ID.

        Attempts direct match first, then tries to resolve secure mapped ID
        to original account number.

        Args:
            cached_result: The cached processing result
            account_id: Account ID to find
            result_id: Result ID for ID mapping resolution

        Returns:
            Dictionary with 'id', 'name', and 'data' keys, or None if not found
        """
        if not cached_result or not hasattr(cached_result, 'data'):
            return None

        # Try direct match
        for acc_id, account_data in cached_result.data.items():
            if acc_id == account_id:
                return {
                    'id': acc_id,
                    'name': getattr(account_data, 'name', None) or f'Account {account_id}',
                    'data': account_data.data if hasattr(account_data, 'data') else []
                }

        # Try resolving secure ID to original account number
        try:
            original_account = self._id_mapping_service.get_account_number(result_id, account_id)
            if original_account:
                for acc_id, account_data in cached_result.data.items():
                    if acc_id == original_account:
                        return {
                            'id': acc_id,
                            'name': getattr(account_data, 'name', None) or f'Account {original_account}',
                            'data': account_data.data if hasattr(account_data, 'data') else []
                        }
        except Exception:
            pass

        return None

    def _filter_rows_by_category(
        self,
        rows: List[AggregatedRow],
        category: str,
    ) -> List[AggregatedRow]:
        """Filter rows by category.

        Args:
            rows: List of AggregatedRow objects
            category: Category name to filter by

        Returns:
            Filtered list of rows matching the category
        """
        return [row for row in rows if hasattr(row, 'category') and row.category == category]

    def _filter_rows_by_month(
        self,
        rows: List[AggregatedRow],
        month_timestamp: str,
    ) -> List[AggregatedRow]:
        """Filter rows by month timestamp.

        Args:
            rows: List of AggregatedRow objects
            month_timestamp: Month timestamp to filter by

        Returns:
            Filtered list of rows matching the month
        """
        return [
            row for row in rows
            if hasattr(row, 'date') and self._extract_month_key(row.date) == month_timestamp
        ]

    def _extract_month_key(self, date_obj: Any) -> str:
        """Extract month key from date object for grouping.

        Args:
            date_obj: DateField or similar object with timestamp or display attribute

        Returns:
            String representation of the month key
        """
        try:
            if hasattr(date_obj, 'timestamp'):
                return str(date_obj.timestamp)
            elif hasattr(date_obj, 'display'):
                return str(date_obj.display)
            else:
                return str(date_obj)
        except Exception:
            return "unknown"

    def _group_rows_by_month(
        self,
        rows: List[AggregatedRow],
    ) -> Dict[str, List[AggregatedRow]]:
        """Group rows by month timestamp.

        Args:
            rows: List of AggregatedRow objects

        Returns:
            Dictionary mapping month keys to lists of rows
        """
        groups: Dict[str, List[AggregatedRow]] = {}
        for row in rows:
            month_key = self._extract_month_key(row.date)
            if month_key not in groups:
                groups[month_key] = []
            groups[month_key].append(row)
        return groups

    def _group_rows_by_category(
        self,
        rows: List[AggregatedRow],
    ) -> Dict[str, List[AggregatedRow]]:
        """Group rows by category.

        Args:
            rows: List of AggregatedRow objects

        Returns:
            Dictionary mapping category names to lists of rows
        """
        groups: Dict[str, List[AggregatedRow]] = {}
        for row in rows:
            category = row.category if hasattr(row, 'category') else 'uncategorized'
            if category not in groups:
                groups[category] = []
            groups[category].append(row)
        return groups

    def _build_months_list(
        self,
        month_groups: Dict[str, List[AggregatedRow]],
        result_id: str,
        account_id: str,
        category_id: str,
        category_name: str,
    ) -> List[Dict[str, Any]]:
        """Build the months list for category months response.

        Args:
            month_groups: Rows grouped by month
            result_id: Processing result ID
            account_id: Account ID
            category_id: Category ID
            category_name: Category name

        Returns:
            List of month dictionaries with aggregated data
        """
        months_list = []

        for month_key in sorted(month_groups.keys(), key=lambda x: x or ''):
            rows = month_groups[month_key]
            first_row = rows[0]

            month_data: Dict[str, Any] = {
                'month': first_row.date.display if hasattr(first_row.date, 'display') else str(first_row.date),
                'month_timestamp': first_row.date.timestamp if hasattr(first_row.date, 'timestamp') else month_key,
                'total': {
                    'display': first_row.total.display if hasattr(first_row.total, 'display') else str(first_row.total),
                    'raw': first_row.total.raw if hasattr(first_row.total, 'raw') else 0.0
                },
                'row_id': first_row.row_id if hasattr(first_row, 'row_id') else '',
                'details': [
                    self._format_detail(detail) for detail in (first_row.details if hasattr(first_row, 'details') else [])
                ]
            }

            # Aggregate totals for all rows in this month
            if len(rows) > 1:
                total_raw = sum(row.total.raw for row in rows if hasattr(row.total, 'raw'))
                month_data['total']['raw'] = total_raw
                month_data['total']['display'] = f"${total_raw:.2f}"

            # Add drilldown URL
            month_identifier = month_data.get('row_id', '')
            month_data['cell_url'] = self._build_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category_id,
                month_id=month_identifier
            )

            months_list.append(month_data)

        return months_list

    def _build_categories_list(
        self,
        category_groups: Dict[str, List[AggregatedRow]],
        result_id: str,
        account_id: str,
        month_id: str,
        month_timestamp: str,
    ) -> List[Dict[str, Any]]:
        """Build the categories list for month categories response.

        Args:
            category_groups: Rows grouped by category
            result_id: Processing result ID
            account_id: Account ID
            month_id: Month ID
            month_timestamp: Month timestamp

        Returns:
            List of category dictionaries with aggregated data
        """
        categories_list = []

        for category in sorted(category_groups.keys(), key=lambda x: x or ''):
            rows = category_groups[category]
            first_row = rows[0]

            category_data: Dict[str, Any] = {
                'category': category,
                'total': {
                    'display': first_row.total.display if hasattr(first_row.total, 'display') else str(first_row.total),
                    'raw': first_row.total.raw if hasattr(first_row.total, 'raw') else 0.0
                },
                'row_id': first_row.row_id if hasattr(first_row, 'row_id') else '',
                'details': [
                    self._format_detail(detail) for detail in (first_row.details if hasattr(first_row, 'details') else [])
                ]
            }

            # Aggregate totals for all rows in this category
            if len(rows) > 1:
                total_raw = sum(row.total.raw for row in rows if hasattr(row.total, 'raw'))
                category_data['total']['raw'] = total_raw
                category_data['total']['display'] = f"${total_raw:.2f}"

            # Add drilldown URL
            category_data['category_url'] = self._build_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category,
                month_id=month_id
            )

            categories_list.append(category_data)

        return categories_list

    def _format_detail(self, detail: Any) -> Dict[str, Any]:
        """Format a detail row for response.

        Args:
            detail: DetailRow or dict-like object

        Returns:
            Formatted detail dictionary
        """
        if hasattr(detail, 'model_dump'):
            return detail.model_dump()
        elif isinstance(detail, dict):
            return detail
        else:
            # Fallback for other types
            return {
                'date': getattr(detail, 'date', {}),
                'amount': getattr(detail, 'amount', {}),
                'merchant': getattr(detail, 'merchant', ''),
                'row_id': getattr(detail, 'row_id', '')
            }

    def _get_category_display_name(
        self,
        rows: List[AggregatedRow],
        category: str,
    ) -> str:
        """Get the display name for a category.

        Args:
            rows: List of AggregatedRow objects
            category: Category name to find

        Returns:
            Formatted category display name
        """
        for row in rows:
            if hasattr(row, 'category') and row.category == category:
                if hasattr(row, 'category_display'):
                    return row.category_display
                break
        # Format as title case with underscores replaced
        return category.replace('_', ' ').title()

    def _get_month_display_name(
        self,
        rows: List[AggregatedRow],
        month_timestamp: str,
    ) -> str:
        """Get the display name for a month.

        Args:
            rows: List of AggregatedRow objects
            month_timestamp: Month timestamp to find

        Returns:
            Formatted month display name
        """
        for row in rows:
            row_month_key = self._extract_month_key(row.date)
            if row_month_key == month_timestamp:
                if hasattr(row.date, 'display'):
                    return row.date.display
                break
        # Format timestamp as date
        try:
            dt = datetime.datetime.fromtimestamp(int(month_timestamp))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return month_timestamp.replace('-', ' ').title()

    def _build_frontend_url(
        self,
        endpoint: str,
        **values: Any
    ) -> str:
        """Generate URL for frontend Vue router routes.

        Args:
            endpoint: Endpoint type ('category_months', 'month_categories', 'category_month_transactions')
            **values: URL parameters (result_id, account_id, category_id, month_id)

        Returns:
            Frontend route URL string
        """
        frontend_routes = {
            'category_months': '/results/{result_id}/accounts/{account_id}/categories/{category_id}/months',
            'month_categories': '/results/{result_id}/accounts/{account_id}/months/{month_id}/categories',
            'category_month_transactions': '/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions'
        }

        if endpoint in frontend_routes:
            return frontend_routes[endpoint].format(**values)
        return "#"

    def _aggregate_highlights_for_drilldown(
        self,
        cached_result: ProcessingResponse,
        groups: Dict[str, List[AggregatedRow]],
        category_filter: Optional[str] = None,
        month_filter: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Aggregate highlights from parent processing result for drilldown rows.

        This is the key method for maintaining consistency with process_transactions.
        Instead of recalculating highlights, we filter the existing highlights
        from the cached result based on which original rows contribute to each
        drilldown aggregation.

        Args:
            cached_result: The cached ProcessingResponse with statistical_metadata
            groups: Rows grouped by the drilldown dimension (month or category)
            category_filter: Optional category filter for additional context
            month_filter: Optional month filter for additional context

        Returns:
            Dictionary mapping drilldown row_ids to aggregated highlight types
        """
        aggregated_highlights: Dict[str, List[str]] = {}

        # Check if we have statistical metadata with highlights
        if not hasattr(cached_result, 'statistical_metadata'):
            return aggregated_highlights

        if not hasattr(cached_result.statistical_metadata, 'highlights'):
            return aggregated_highlights

        # Build lookup for original highlights from parent processing
        original_highlights: Dict[str, List[str]] = {}
        for cell_highlight in cached_result.statistical_metadata.highlights:
            original_highlights[cell_highlight.row_id] = cell_highlight.highlight_types

        if not original_highlights:
            return aggregated_highlights

        # For each drilldown group, aggregate highlights from contributing rows
        for group_key, rows in groups.items():
            # Collect all original row_ids that contribute to this aggregation
            contributing_row_ids: List[str] = []
            for row in rows:
                if hasattr(row, 'row_id'):
                    contributing_row_ids.append(row.row_id)

            # Aggregate highlights for these row_ids
            combined_highlights: List[str] = []
            for row_id in contributing_row_ids:
                if row_id in original_highlights:
                    combined_highlights.extend(original_highlights[row_id])

            # Remove duplicates while preserving order
            seen = set()
            unique_highlights = []
            for h in combined_highlights:
                if h not in seen:
                    seen.add(h)
                    unique_highlights.append(h)

            if unique_highlights:
                # Use the first row's row_id as the drilldown row identifier
                if rows and hasattr(rows[0], 'row_id'):
                    drilldown_row_id = rows[0].row_id
                    aggregated_highlights[drilldown_row_id] = unique_highlights

        return aggregated_highlights

    def get_category_month_transactions_response(
        self,
        result_id: str,
        account_id: str,
        category_id: str,
        month_id: str,
    ) -> Dict[str, Any]:
        """Build response for category month transactions drilldown endpoint.

        Retrieves cached processing result, filters by account, category, and month,
        and extracts individual transaction details.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to filter by
            month_id: Secure month ID to filter by

        Returns:
            Dictionary with structure:
            - result_id: Processing result ID
            - account_id: Account ID
            - account_name: Account name
            - category_id: Category ID
            - category_name: Resolved category name
            - month_id: Month ID
            - month_name: Resolved month name
            - data: List of transaction details
            - highlights: Highlights for the transactions

        Raises:
            ValueError: If result, account, category, or month not found or no transactions
        """
        # Get cached result
        cached_result = self._cache_service.get(result_id)
        if not cached_result:
            raise ValueError('Results not found')

        # Find account data
        account_data = self._find_account_data(cached_result, account_id, result_id)
        if not account_data:
            raise ValueError('Account not found in results')

        # Resolve secure category_id and month_id to original values
        try:
            original_category = self._id_mapping_service.get_category_name(result_id, category_id)
        except Exception:
            original_category = category_id  # Fallback to direct use

        try:
            original_month_ts = self._id_mapping_service.get_month_timestamp(month_id)
        except Exception:
            original_month_ts = month_id  # Fallback to direct use

        if original_category is None or original_month_ts is None:
            raise ValueError('Category or month not found')

        category_name = original_category.replace('_', ' ').title()
        month_name = original_month_ts.replace('-', ' ').title()

        transactions = []

        for row in account_data['data']:
            row_category = row.category if hasattr(row, 'category') else 'uncategorized'
            row_month_key = self._extract_month_key(row.date)

            if row_category == original_category and row_month_key == original_month_ts:
                if hasattr(row, 'category_display'):
                    category_name = row.category_display
                if hasattr(row.date, 'display'):
                    month_name = row.date.display

                if hasattr(row, 'details') and row.details:
                    for detail in row.details:
                        detail_dict = self._format_detail(detail)

                        date_obj = detail_dict.get('date', {})
                        amount_obj = detail_dict.get('amount', {})

                        transaction_data = {
                            'date': {
                                'display': date_obj.get('display', '') if isinstance(date_obj, dict) else str(date_obj)
                            },
                            'amount': {
                                'display': amount_obj.get('display', '') if isinstance(amount_obj, dict) else str(amount_obj)
                            },
                            'merchant': detail_dict.get('merchant', ''),
                            'row_id': detail_dict.get('row_id', '')
                        }
                        transactions.append(transaction_data)

        if not transactions:
            raise ValueError('No transactions found for the specified category and month')

        response_data: Dict[str, Any] = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'category_id': category_id,
            'category_name': category_name,
            'month_id': month_id,
            'month_name': month_name,
            'data': transactions
        }

        # Extract highlights from statistical_metadata
        if hasattr(cached_result, 'statistical_metadata') and hasattr(cached_result.statistical_metadata, 'highlights'):
            highlights_dict: Dict[str, List[str]] = {}
            for cell_highlight in cached_result.statistical_metadata.highlights:
                highlights_dict[cell_highlight.row_id] = cell_highlight.highlight_types
            if highlights_dict:
                response_data['highlights'] = highlights_dict

        return response_data
