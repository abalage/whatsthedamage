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
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from whatsthedamage.models.domain.dt_models import ProcessingResponse, AggregatedRow, AccountResponse
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.models.api.responses import (
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    MonthData,
    CategoryData,
    TransactionDetail,
)
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
    ) -> CategoryMonthsApiResponse:
        """Build response for category months drilldown endpoint.

        Retrieves cached processing result, filters by account and category,
        groups transactions by month, aggregates totals, and aggregates highlights
        from the original processing result.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to get months for

        Returns:
            CategoryMonthsApiResponse: Typed response for /results/<id>/accounts/<acct>/categories/<cat>/months

        Raises:
            ValueError: If result, account, or category not found
        """
        cached_result = self._get_cached_result(result_id)
        account_data = self._get_account_data(cached_result, account_id, result_id)

        # Resolve category ID to original name
        original_category = self._id_mapping_service.get_category_name(result_id, category_id)
        if not original_category:
            original_category = category_id

        # Filter rows by category_id and group by month
        category_rows = self._filter_rows(account_data['data'], 'category_id', original_category)
        month_groups = self._group_rows(category_rows, lambda r: self._extract_month_key(r.date))

        if not month_groups:
            raise ValueError('Category not found or has no data')

        # Build response data - convert to MonthData DTOs
        months_list: List[MonthData] = []
        for month_ts, rows in month_groups.items():
            first_row = rows[0]
            row_id = getattr(first_row, 'row_id', '')

            # Build total dict
            total_dict = self._build_item_total(first_row, rows)

            # Build cell_url (drilldown to transactions for this month)
            cell_url = self._build_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category_id,
                month_id=month_ts
            )

            # Convert timestamp to human-readable month format (e.g., "January 2024")
            if month_ts:
                dt = datetime.datetime.fromtimestamp(int(month_ts))
                month_name = DateConverter.convert_month_number_to_name(dt.month)
                month_display = f"{month_name} {dt.year}"
            else:
                month_display = "Unknown"
            months_list.append(MonthData(
                month=month_display,
                month_timestamp=int(month_ts) if month_ts else 0,
                total=total_dict,
                row_id=row_id,
                cell_url=cell_url
            ))

        # Aggregate highlights for drilldown rows
        highlights = self._aggregate_highlights_for_drilldown(
            cached_result, month_groups, category_filter=original_category
        )

        return CategoryMonthsApiResponse(
            result_id=result_id,
            account_id=account_id,
            account_name=account_data['name'],
            category_id=category_id,
            data=months_list,
            highlights=highlights
        )

    def get_month_categories_response(
        self,
        result_id: str,
        account_id: str,
        month_id: str,
    ) -> MonthCategoriesApiResponse:
        """Build response for month categories drilldown endpoint.

        Retrieves cached processing result, filters by account and month,
        groups transactions by category, aggregates totals, and aggregates highlights
        from the original processing result.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            month_id: Secure month ID to get categories for

        Returns:
            MonthCategoriesApiResponse: Typed response for /results/<id>/accounts/<acct>/months/<month>/categories

        Raises:
            ValueError: If result, account, or month not found
        """
        cached_result = self._get_cached_result(result_id)
        account_data = self._get_account_data(cached_result, account_id, result_id)

        # Resolve month ID to original timestamp
        original_month_ts = self._id_mapping_service.get_month_timestamp(month_id)
        if not original_month_ts:
            original_month_ts = month_id

        # Filter rows by month and group by category
        month_rows = self._filter_rows(account_data['data'], 'date', original_month_ts, self._extract_month_key)
        category_groups = self._group_rows(month_rows, lambda r: getattr(r, 'category_id', 'uncategorized'))

        if not category_groups:
            raise ValueError('Month not found or has no data')

        # Build response data - convert to CategoryData DTOs
        categories_list: List[CategoryData] = []
        for category, rows in category_groups.items():
            first_row = rows[0]
            row_id = getattr(first_row, 'row_id', '')

            # Build total dict
            total_dict = self._build_item_total(first_row, rows)

            # Build category_url (drilldown to transactions for this category)
            category_url = self._build_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category,
                month_id=original_month_ts
            )

            categories_list.append(CategoryData(
                category=category,
                total=total_dict,
                row_id=row_id,
                category_url=category_url
            ))

        # Get month display name
        def format_month_name(v: str) -> str:
            dt = datetime.datetime.fromtimestamp(int(v))
            month_name_loc = DateConverter.convert_month_number_to_name(dt.month)
            return f"{month_name_loc} {dt.year}"

        month_name = self._get_display_name(
            account_data['data'], original_month_ts, 'date', 'display',
            format_month_name
        )

        # Aggregate highlights for drilldown rows
        highlights = self._aggregate_highlights_for_drilldown(
            cached_result, category_groups, category_filter=None, month_filter=original_month_ts
        )

        return MonthCategoriesApiResponse(
            result_id=result_id,
            account_id=account_id,
            account_name=account_data['name'],
            month_id=month_id,
            month_name=month_name,
            data=categories_list,
            highlights=highlights
        )

    def _get_cached_result(self, result_id: str) -> ProcessingResponse:
        """Get and validate cached result.

        Args:
            result_id: UUID of the cached processing result

        Returns:
            The cached ProcessingResponse

        Raises:
            ValueError: If result not found
        """
        cached_result = self._cache_service.get(result_id)
        if not cached_result:
            raise ValueError('Results not found')
        return cast(ProcessingResponse, cached_result)

    def _get_account_data(
        self,
        cached_result: ProcessingResponse,
        account_id: str,
        result_id: str
    ) -> Dict[str, Any]:
        """Get and validate account data with secure ID resolution.

        Args:
            cached_result: The cached processing result
            account_id: Account ID to find
            result_id: Result ID for ID mapping resolution

        Returns:
            Dictionary with 'id', 'name', and 'data' keys

        Raises:
            ValueError: If account not found in results
        """
        account_data = self._find_account_data(cached_result, account_id, result_id)
        if not account_data:
            raise ValueError('Account not found in results')
        return account_data

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

        account_ids_to_try = [account_id]

        # Add resolved secure ID if different from account_id
        try:
            original_account = self._id_mapping_service.get_account_number(result_id, account_id)
            if original_account and original_account != account_id:
                account_ids_to_try.append(original_account)
        except Exception:
            pass

        for acc_id in account_ids_to_try:
            for existing_id, account_data in cached_result.data.items():
                if acc_id == existing_id:
                    return {
                        'id': existing_id,
                        'name': getattr(account_data, 'name', None) or f'Account {existing_id}',
                        'data': getattr(account_data, 'data', [])
                    }

        return None



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

    def _filter_rows(
        self,
        rows: List[AggregatedRow],
        field: str,
        value: str,
        transform: Optional[Callable[[Any], str]] = None
    ) -> List[AggregatedRow]:
        """Filter rows by field value with optional transformation.

        Args:
            rows: List of AggregatedRow objects
            field: Field name to check
            value: Value to match
            transform: Optional function to transform field value before comparison

        Returns:
            Filtered list of rows matching the criteria
        """
        result = []
        for row in rows:
            row_value = getattr(row, field, None) if hasattr(row, field) else None
            if row_value is not None and transform is not None:
                row_value = transform(row_value)
            if row_value == value:
                result.append(row)
        return result

    def _group_rows(
        self,
        rows: List[AggregatedRow],
        key_func: Callable[[AggregatedRow], str]
    ) -> Dict[str, List[AggregatedRow]]:
        """Group rows by key function.

        Args:
            rows: List of AggregatedRow objects
            key_func: Function to extract grouping key from a row

        Returns:
            Dictionary mapping keys to lists of rows
        """
        groups: Dict[str, List[AggregatedRow]] = {}
        for row in rows:
            key = key_func(row)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        return groups

    def _get_display_name(
        self,
        rows: List[AggregatedRow],
        value: str,
        match_field: str,
        display_field: str,
        fallback_formatter: Callable[[str], str]
    ) -> str:
        """Get display name for an entity by searching rows.

        Args:
            rows: List of AggregatedRow objects to search
            value: Value to match in match_field
            match_field: Field name to match against value
            display_field: Field name containing display value
            fallback_formatter: Function to format value if not found in rows

        Returns:
            Display name or formatted fallback
        """
        for row in rows:
            if getattr(row, match_field, None) == value:
                display = getattr(row, display_field, None)
                if display:
                    return str(display)
                break
        return fallback_formatter(value)



    def _get_nested_attr(self, obj: Any, attr_path: str, fallback: Any) -> Any:
        """Get nested attribute from object using dot-separated path.

        Args:
            obj: Object to get attribute from
            attr_path: Dot-separated attribute path (e.g., 'date.display')
            fallback: Value to return if attribute not found

        Returns:
            Attribute value or fallback
        """
        if not obj or not attr_path:
            return fallback
        value = obj
        for part in attr_path.split('.'):
            if value is None:
                return fallback
            value = getattr(value, part, None)
            if value is None:
                return fallback
        return value

    def _build_item_total(self, first_row: AggregatedRow, rows: List[AggregatedRow]) -> Dict[str, Any]:
        """Build total dictionary for an item, aggregating if multiple rows.

        Args:
            first_row: First row in the group
            rows: All rows in the group

        Returns:
            Total dictionary with 'display' and 'raw' keys
        """
        if len(rows) > 1:
            total_raw = sum(getattr(row.total, 'raw', 0.0) for row in rows)
            return {'display': f"${total_raw:.2f}", 'raw': total_raw}
        return {
            'display': getattr(first_row.total, 'display', str(first_row.total)),
            'raw': getattr(first_row.total, 'raw', 0.0)
        }

    def _build_drilldown_item_url(
        self,
        endpoint: str,
        result_id: str,
        account_id: str,
        fixed_category_id: str,
        fixed_month_id: str,
        primary_field: str,
        key: str,
        row_id: str,
        use_row_id_as_month: bool
    ) -> str:
        """Build drilldown URL for an item.

        Args:
            endpoint: URL endpoint name
            result_id: Processing result ID
            account_id: Account ID
            fixed_category_id: Fixed category ID for months list
            fixed_month_id: Fixed month ID for categories list
            primary_field: 'month' or 'category'
            key: Group key (month timestamp or category name)
            row_id: Row ID from first row
            use_row_id_as_month: Whether to use row_id as month_id

        Returns:
            Formatted frontend URL
        """
        if primary_field == 'month':
            month_id = row_id if use_row_id_as_month else key
            return self._build_frontend_url(
                endpoint, result_id=result_id, account_id=account_id,
                category_id=fixed_category_id, month_id=month_id
            )
        # category
        return self._build_frontend_url(
            endpoint, result_id=result_id, account_id=account_id,
            category_id=key, month_id=fixed_month_id
        )

    def _build_grouped_list(
        self,
        groups: Dict[str, List[AggregatedRow]],
        result_id: str,
        account_id: str,
        fixed_category_id: str,
        fixed_month_id: str,
        endpoint: str,
        primary_field: str,
        display_attr: str,
        timestamp_attr: Optional[str] = None,
        url_field: str = 'cell_url',
        use_row_id_as_month: bool = False,
    ) -> List[Dict[str, Any]]:
        """Generic builder for grouped drilldown lists.

        Builds a list of dictionaries from grouped rows, with aggregated totals
        and drilldown URLs. This unifies the months and categories list building.

        Args:
            groups: Rows grouped by a key
            result_id: Processing result ID
            account_id: Account ID
            fixed_category_id: Fixed category ID for URLs (or empty if using group key)
            fixed_month_id: Fixed month ID for URLs (or empty if using group key)
            endpoint: Frontend route endpoint name
            primary_field: Field name for the group key ('month' or 'category')
            display_attr: Attribute path for display value
            timestamp_attr: Optional attribute path for timestamp
            url_field: URL field name ('cell_url' or 'category_url')
            use_row_id_as_month: If True, use row_id as month_id in URLs

        Returns:
            List of dictionaries with aggregated data and URLs
        """
        items_list = []

        for key in sorted(groups.keys(), key=lambda x: x or ''):
            rows = groups[key]
            first_row = rows[0]
            row_id = getattr(first_row, 'row_id', '')

            item_data: Dict[str, Any] = {
                primary_field: self._get_nested_attr(first_row, display_attr, str(key)),
                'total': self._build_item_total(first_row, rows),
                'row_id': row_id,
                'details': [self._format_detail(d) for d in getattr(first_row, 'details', [])],
            }

            if timestamp_attr:
                item_data[f'{primary_field}_timestamp'] = self._get_nested_attr(
                    first_row, timestamp_attr, key
                )

            item_data[url_field] = self._build_drilldown_item_url(
                endpoint, result_id, account_id, fixed_category_id, fixed_month_id,
                primary_field, key, row_id, use_row_id_as_month
            )

            items_list.append(item_data)

        return items_list

    def _format_detail(self, detail: Any) -> Dict[str, Any]:
        """Format a detail row for response.

        Args:
            detail: DetailRow or dict-like object

        Returns:
            Formatted detail dictionary
        """
        if hasattr(detail, 'model_dump'):
            return cast(Dict[str, Any], detail.model_dump())
        if isinstance(detail, dict):
            return detail
        # For Pydantic models without model_dump or dataclass instances
        return {
            'date': getattr(detail, 'date', {}),
            'amount': getattr(detail, 'amount', {}),
            'merchant': getattr(detail, 'merchant', ''),
            'notice': getattr(detail, 'notice', None),
            'row_id': getattr(detail, 'row_id', '')
        }





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

    def _get_empty_url_response(self) -> Dict[str, Any]:
        """Return empty URL response structure."""
        return {
            'account_id': None,
            'category_urls': {},
            'month_urls': {},
            'cell_urls': {}
        }

    def _process_category_url(
        self,
        row: Any,
        result_id: str,
        account_id: str,
        category_urls: Dict[str, Dict[str, str]]
    ) -> None:
        """Process category URL for a row if not already processed.

        Args:
            row: Data row containing category information
            result_id: Processing result ID
            account_id: Secure account ID
            category_urls: Dictionary to store category URLs
        """
        category = getattr(row, 'category_id', None)
        if category and category not in category_urls:
            category_id = self._id_mapping_service.get_category_id(result_id, category) or category
            category_str = cast(str, category)
            category_id_str = cast(str, category_id)
            category_urls[category_str] = {
                'category_url': self._build_frontend_url(
                    'category_months',
                    result_id=result_id,
                    account_id=account_id,
                    category_id=category_id_str
                ),
                'category_id': category_id_str
            }

    def _process_month_url(
        self,
        row: Any,
        result_id: str,
        account_id: str,
        month_urls: Dict[str, Dict[str, str]]
    ) -> None:
        """Process month URL for a row if not already processed.

        Args:
            row: Data row containing date information
            result_id: Processing result ID
            account_id: Secure account ID
            month_urls: Dictionary to store month URLs
        """
        date_obj = getattr(row, 'date', None)
        if date_obj and hasattr(date_obj, 'timestamp') and date_obj.timestamp:
            month_ts = str(date_obj.timestamp)
            if month_ts not in month_urls:
                month_id = self._id_mapping_service.get_month_id(month_ts) or month_ts
                month_urls[month_ts] = {
                    'month_url': self._build_frontend_url(
                        'month_categories',
                        result_id=result_id,
                        account_id=account_id,
                        month_id=month_id
                    ),
                    'month_id': month_id
                }

    def _process_cell_url(
        self,
        row: Any,
        result_id: str,
        account_id: str,
        cell_urls: Dict[str, Dict[str, str]]
    ) -> None:
        """Process cell URL for a row.

        Args:
            row: Data row containing category, date, and row_id
            result_id: Processing result ID
            account_id: Secure account ID
            cell_urls: Dictionary to store cell URLs
        """
        category = getattr(row, 'category_id', None)
        date_obj = getattr(row, 'date', None)
        row_id = getattr(row, 'row_id', None)
        if category and date_obj and row_id and hasattr(date_obj, 'timestamp') and date_obj.timestamp:
            category_id = self._id_mapping_service.get_category_id(result_id, category) or category
            month_id = self._id_mapping_service.get_month_id(str(date_obj.timestamp)) or str(date_obj.timestamp)
            row_id_str = cast(str, row_id)
            cell_urls[row_id_str] = {
                'cell_url': self._build_frontend_url(
                    'category_month_transactions',
                    result_id=result_id,
                    account_id=account_id,
                    category_id=category_id,
                    month_id=month_id
                ),
                'category_id': category_id,
                'month_id': month_id
            }

    def generate_drilldown_urls(
        self,
        result_id: str,
        account_number: Optional[str],
        dt_response: Optional[AccountResponse]
    ) -> Dict[str, Any]:
        """Generate all drill-down URLs for a result using ID mapping.

        Encapsulates the URL generation logic that involves business rules
        for mapping sensitive data to secure IDs.

        Args:
            result_id: Processing result ID
            account_number: Original account number
            dt_response: AccountResponse containing the data

        Returns:
            Dictionary containing pre-generated URLs for all drill-down levels
        """
        if not account_number or not dt_response:
            return self._get_empty_url_response()

        account_id = self._id_mapping_service.get_account_id(result_id, account_number)
        if not account_id:
            return self._get_empty_url_response()

        category_urls: Dict[str, Dict[str, str]] = {}
        month_urls: Dict[str, Dict[str, str]] = {}
        cell_urls: Dict[str, Dict[str, str]] = {}

        for row in dt_response.data:
            self._process_category_url(row, result_id, account_id, category_urls)
            self._process_month_url(row, result_id, account_id, month_urls)
            self._process_cell_url(row, result_id, account_id, cell_urls)

        return {
            'account_id': account_id,
            'category_urls': category_urls,
            'month_urls': month_urls,
            'cell_urls': cell_urls
        }

    def _get_highlights_lookup(self, cached_result: ProcessingResponse) -> Dict[str, List[str]]:
        """Build a lookup dictionary for highlights from cached result.

        Args:
            cached_result: ProcessingResponse to extract highlights from

        Returns:
            Dictionary mapping row_ids to list of highlight types, or empty dict if not available
        """
        if not hasattr(cached_result, 'statistical_metadata'):
            return {}
        if not hasattr(cached_result.statistical_metadata, 'highlights'):
            return {}

        # Merge highlight types for same row_id to match recalculate endpoint behavior
        # A row can have multiple CellHighlight entries (one per algorithm)
        highlights_dict: Dict[str, List[str]] = {}
        for cell_highlight in cached_result.statistical_metadata.highlights:
            if cell_highlight.row_id in highlights_dict:
                highlights_dict[cell_highlight.row_id].extend(cell_highlight.highlight_types)
            else:
                highlights_dict[cell_highlight.row_id] = cell_highlight.highlight_types.copy()
        return highlights_dict

    def _row_passes_filters(
        self,
        row: AggregatedRow,
        category_filter: Optional[str],
        month_filter: Optional[str]
    ) -> bool:
        """Check if a row passes the given category and month filters.

        Args:
            row: AggregatedRow to check
            category_filter: Optional category to filter by
            month_filter: Optional month timestamp to filter by

        Returns:
            True if row has a row_id and passes all provided filters
        """
        if not hasattr(row, 'row_id'):
            return False
        if category_filter and hasattr(row, 'category_id'):
            if str(row.category_id) != category_filter:
                return False
        if month_filter and hasattr(row, 'date'):
            if self._extract_month_key(row.date) != month_filter:
                return False
        return True

    def _aggregate_unique_highlights(
        self,
        row_ids: List[str],
        highlights_lookup: Dict[str, List[str]]
    ) -> List[str]:
        """Aggregate unique highlights from a list of row IDs.

        Args:
            row_ids: List of row IDs to aggregate highlights from
            highlights_lookup: Dictionary mapping row_ids to highlight types

        Returns:
            List of unique highlight types in order of first appearance
        """
        seen = set()
        unique_highlights = []
        for row_id in row_ids:
            for h in highlights_lookup.get(row_id, []):
                if h not in seen:
                    seen.add(h)
                    unique_highlights.append(h)
        return unique_highlights

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

        highlights_lookup = self._get_highlights_lookup(cached_result)
        if not highlights_lookup:
            return aggregated_highlights

        for group_key, rows in groups.items():
            # Collect row_ids that pass filters
            contributing_row_ids = [
                row.row_id for row in rows
                if self._row_passes_filters(row, category_filter, month_filter)
            ]

            # Aggregate unique highlights
            unique_highlights = self._aggregate_unique_highlights(
                contributing_row_ids, highlights_lookup
            )

            if unique_highlights and rows and hasattr(rows[0], 'row_id'):
                aggregated_highlights[rows[0].row_id] = unique_highlights

        return aggregated_highlights

    def _resolve_category_and_month(
        self,
        result_id: str,
        category_id: str,
        month_id: str
    ) -> Tuple[str, str]:
        """Resolve secure category and month IDs to original values with fallback.

        Args:
            result_id: Processing result ID
            category_id: Secure category ID
            month_id: Secure month ID

        Returns:
            Tuple of (original_category, original_month_ts)
        """
        try:
            original_category = self._id_mapping_service.get_category_name(result_id, category_id)
        except Exception:
            original_category = category_id
        if original_category is None:
            original_category = category_id
        try:
            original_month_ts = self._id_mapping_service.get_month_timestamp(month_id)
        except Exception:
            original_month_ts = month_id
        if original_month_ts is None:
            original_month_ts = month_id
        return original_category, original_month_ts

    def _row_matches_filters(
        self,
        row: AggregatedRow,
        category: str,
        month_ts: str
    ) -> bool:
        """Check if a row matches the given category and month filters.

        Args:
            row: AggregatedRow to check
            category: Category to match
            month_ts: Month timestamp to match

        Returns:
            True if row matches both filters
        """
        row_category = getattr(row, 'category_id', 'uncategorized')
        row_month_key = self._extract_month_key(getattr(row, 'date', None))
        return row_category == category and row_month_key == month_ts

    def _format_transaction_detail(self, detail: Any) -> Dict[str, Any]:
        """Format a detail object into transaction data structure.

        Args:
            detail: Detail object to format

        Returns:
            Formatted transaction dictionary
        """
        detail_dict = self._format_detail(detail)
        # Extract date with both display and timestamp
        date_obj = detail_dict.get('date', {})
        if isinstance(date_obj, dict):
            date_formatted = {
                'display': self._get_display_value(date_obj),
                'timestamp': date_obj.get('timestamp', '')
            }
        else:
            date_formatted = {'display': str(date_obj), 'timestamp': ''}

        # Extract amount with both display and raw
        amount_obj = detail_dict.get('amount', {})
        if isinstance(amount_obj, dict):
            amount_formatted = {
                'display': self._get_display_value(amount_obj),
                'raw': amount_obj.get('raw', 0.0)
            }
        else:
            amount_formatted = {'display': str(amount_obj), 'raw': amount_obj if amount_obj is not None else 0.0}

        return {
            'date': date_formatted,
            'amount': amount_formatted,
            'merchant': detail_dict.get('merchant', ''),
            'notice': detail_dict.get('notice', None),
            'row_id': detail_dict.get('row_id', '')
        }

    def _get_display_value(self, value: Any) -> str:
        """Get display value from a value that might be a dict or other type.

        Args:
            value: Value to get display from

        Returns:
            Display string value
        """
        if isinstance(value, dict):
            return str(value.get('display', ''))
        return str(value)

    def _extract_transactions(
        self,
        rows: List[AggregatedRow],
        category: str,
        month_ts: str
    ) -> List[Dict[str, Any]]:
        """Extract transaction data from rows matching category and month.

        Args:
            rows: List of AggregatedRow objects
            category: Category to filter by
            month_ts: Month timestamp to filter by

        Returns:
            List of formatted transaction dictionaries
        """
        transactions = []
        for row in rows:
            if not self._row_matches_filters(row, category, month_ts):
                continue
            for detail in getattr(row, 'details', []):
                transactions.append(self._format_transaction_detail(detail))
        return transactions

    def _extract_highlights_dict(self, cached_result: ProcessingResponse) -> Optional[Dict[str, List[str]]]:
        """Extract highlights dictionary from cached result.

        Args:
            cached_result: ProcessingResponse to extract from

        Returns:
            Dictionary mapping row_ids to highlight types, or None if not available
        """
        if not hasattr(cached_result, 'statistical_metadata'):
            return None
        if not hasattr(cached_result.statistical_metadata, 'highlights'):
            return None
        return {
            cell_highlight.row_id: cell_highlight.highlight_types
            for cell_highlight in cached_result.statistical_metadata.highlights
        }

    def get_category_month_transactions_response(
        self,
        result_id: str,
        account_id: str,
        category_id: str,
        month_id: str,
    ) -> CategoryMonthTransactionsApiResponse:
        """Build response for category month transactions drilldown endpoint.

        Retrieves cached processing result, filters by account, category, and month,
        and extracts individual transaction details.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to filter by
            month_id: Secure month ID to filter by

        Returns:
            CategoryMonthTransactionsApiResponse: Typed response for /results/<id>/accounts/<acct>/categories/<cat>/months/<month>/transactions

        Raises:
            ValueError: If result, account, category, or month not found or no transactions
        """
        cached_result = self._get_cached_result(result_id)
        account_data = self._get_account_data(cached_result, account_id, result_id)

        original_category, original_month_ts = self._resolve_category_and_month(
            result_id, category_id, month_id
        )

        if original_category is None or original_month_ts is None:
            raise ValueError('Category or month not found')

        # Get display names with better fallback
        category_name = self._get_display_name(
            account_data['data'], original_category, 'category', 'category_display',
            lambda v: v.replace('_', ' ').title()
        )

        def format_month_name(v: str) -> str:
            if v.isdigit():
                dt = datetime.datetime.fromtimestamp(int(v))
                month_name_loc = DateConverter.convert_month_number_to_name(dt.month)
                return f"{month_name_loc} {dt.year}"
            return v.replace('-', ' ').title()

        month_name = self._get_display_name(
            account_data['data'], original_month_ts, 'date', 'display',
            format_month_name
        )

        # Extract transactions and convert to TransactionDetail DTOs
        transactions_dicts = self._extract_transactions(
            account_data['data'], original_category, original_month_ts
        )

        if not transactions_dicts:
            raise ValueError('No transactions found for the specified category and month')

        transactions: List[TransactionDetail] = []
        for tx_dict in transactions_dicts:
            # _format_transaction_detail returns a dict with date, amount, merchant, row_id
            # We need to convert it to TransactionDetail format
            # Note: TransactionDetail expects date.timestamp as string, so convert int to str
            timestamp = tx_dict.get('date', {}).get('timestamp', '')
            if isinstance(timestamp, int):
                timestamp = str(timestamp)
            transactions.append(TransactionDetail(
                date={'display': tx_dict.get('date', {}).get('display', ''), 'timestamp': timestamp},
                amount={'display': tx_dict.get('amount', {}).get('display', ''), 'raw': tx_dict.get('amount', {}).get('raw', 0.0)},
                merchant=tx_dict.get('merchant', ''),
                notice=tx_dict.get('notice', None),
                currency='',
                type='',
                confidence=None,
                row_id=tx_dict.get('row_id', ''),
                category_id=category_id,
                month_id=month_id
            ))

        highlights_dict = self._extract_highlights_dict(cached_result)

        return CategoryMonthTransactionsApiResponse(
            result_id=result_id,
            account_id=account_id,
            account_name=account_data['name'],
            category_id=category_id,
            month_id=month_id,
            month_name=month_name,
            data=transactions,
            highlights=highlights_dict
        )
