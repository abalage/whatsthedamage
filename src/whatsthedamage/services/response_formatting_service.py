"""Response Formatting Service combining data formatting and response building.

This service merges the functionality of DataFormattingService and ResponseBuilderService
to provide a unified interface for all output formatting and response building needs.

Architecture Patterns:
- Strategy Pattern: Different formatting strategies per output type
- Adapter Pattern: Adapt DataFrame to various output formats
- Factory Pattern: Create appropriate formatter based on output type
- Decorator Pattern: Add features (sorting, currency) to base formatters
- Builder Pattern: Complex response objects built step-by-step
- Facade Pattern: Simplifies complex response building logic
- Template Method: Common structure, variant implementations
- DRY Principle: Single implementation for formatting and response building operations
"""
import pandas as pd
import json
from typing import Dict, Optional, Any, List, TYPE_CHECKING
from whatsthedamage.models.domain.dt_models import AccountResponse, StatisticalMetadata, SummaryData, DetailedResponse, ProcessingResponse
from whatsthedamage.models.api.common import ProcessingMetadata, ErrorResponse
from whatsthedamage.models.api.requests import ProcessingRequest
from whatsthedamage.models.api.responses import (
    ResultsApiResponse,
    AccountsDataResponse,
    AccountDataResponse,
    DrilldownUrls,
    DrilldownUrlInfo,
    MonthUrlInfo,
    CellUrlInfo,
)
from gettext import gettext as _
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.interfaces import IDataFormattingService
from whatsthedamage.utils.logging import get_logger

if TYPE_CHECKING:
    from flask import Response


class ResponseFormattingService(IDataFormattingService):
    """Service for formatting data and building responses.

    Combines the functionality of DataFormattingService and ResponseBuilderService.
    Supports multiple output formats and response types:
    - HTML tables (with optional sorting metadata)
    - CSV strings
    - JSON strings
    - Currency formatting
    - API detailed responses
    - Error responses

    Account aware.
    """

    def __init__(self, statistical_analysis_service: Optional[StatisticalAnalysisService] = None) -> None:
        """Initialize the response formatting service."""
        self.statistical_analysis_service = statistical_analysis_service
        self._categories_header = _("Categories")
        self.logger = get_logger(__name__)

    # Data Formatting Methods (from DataFormattingService)

    def format_account_id(self, account_number: str) -> str:
        """Format account ID by adding dashes every 8 digits.

        This utility method provides consistent account ID formatting across
        all interfaces (CLI, Web, API).

        :param account_number: Raw account ID string
        :return: Formatted account ID with dashes every 8 digits
        """
        formatted_id = '-'.join(
                    account_number[i:i+8]
                    for i in range(0, len(account_number), 8)
                )
        return formatted_id

    def format_as_html_table(
        self,
        data: Dict[str, Dict[str, float]],
        nowrap: bool = False
    ) -> str:
        """Format data as HTML table with optional sorting.

        :param data: Data dictionary where outer keys are column headers (time periods),
            inner keys are rows (categories), values are amounts
        :param nowrap: If True, disables text wrapping in pandas output
        :return: HTML string with formatted table

        Example::

            >>> data = {"Total": {"Grocery": 150.5, "Utilities": 80.0}}
            >>> html = service.format_as_html_table(data)
            >>> assert "150.5" in html
        """
        # Configure pandas display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        if nowrap:
            pd.set_option('display.expand_frame_repr', False)

        # Create DataFrame from data
        df = pd.DataFrame(data)

        # Replace NaN values with 0
        df = df.fillna(0)

        # Sort by index (categories)
        df = df.sort_index()

        # Convert to HTML
        html = df.to_html(border=0)

        # Replace empty header with categories header
        html = html.replace('<th></th>', f'<th>{self._categories_header}</th>', 1)

        return html

    def format_as_csv(
        self,
        data: Dict[str, Dict[str, float]],
        delimiter: str = ',',
    ) -> str:
        """Format data as CSV string.

        :param data: Data dictionary where outer keys are column headers (time periods),
            inner keys are rows (categories), values are amounts
        :param delimiter: CSV delimiter character
        :return: CSV formatted string

        Example::

            >>> data = {"January": {"Grocery": 150.5}}
            >>> csv = service.format_as_csv(data)
            >>> assert "Grocery,150.5" in csv
        """
        # Create DataFrame
        df = pd.DataFrame(data)
        df = df.fillna(0)
        df = df.sort_index()

        # Convert to CSV string
        return df.to_csv(sep=delimiter)

    def format_as_string(
        self,
        data: Dict[str, Dict[str, float]],
        nowrap: bool = False
    ) -> str:
        """Format data as plain string for console output.

        :param data: Data dictionary where outer keys are column headers (time periods),
            inner keys are rows (categories), values are amounts
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Plain text formatted string

        Example::

            >>> data = {"Total": {"Grocery": 150.5}}
            >>> text = service.format_as_string(data)
            >>> assert "Grocery" in text and "150.5" in text
        """
        # Configure pandas display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        if nowrap:
            pd.set_option('display.expand_frame_repr', False)

        # Create DataFrame
        df = pd.DataFrame(data)
        df = df.fillna(0)
        df = df.sort_index()

        return df.to_string()

    def format_as_json(
        self,
        data: Dict[str, Any],
        pretty: bool = False
    ) -> str:
        """Format data as JSON string.

        :param data: Data dictionary to serialize
        :param pretty: If True, formats JSON with indentation
        :return: JSON formatted string

        Example::

            >>> data = {"grocery": 150.5, "utilities": 80.0}
            >>> json_str = service.format_as_json(data)
            >>> assert "grocery" in json_str
        """
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def format_currency(
        self,
        value: float,
        currency: str,
        decimal_places: int = 2
    ) -> str:
        """Format currency value for display.

        :param value: Numeric value to format
        :param currency: Currency code (e.g., "EUR", "USD")
        :param decimal_places: Number of decimal places
        :return: Formatted currency string

        Example::

            >>> formatted = service.format_currency(150.567, "EUR")
            >>> assert formatted == "150.57 EUR"

        .. note::
            Simple formatting is used. Can be extended with babel/locale
            support in the future if needed.
        """
        return f"{value:.{decimal_places}f} {currency}"

    def format_for_output(
        self,
        data: Dict[str, Dict[str, float]],
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format data for various output types (HTML, CSV file, or console string).

        This is a convenience method that consolidates the common formatting logic
        used across CLI and CSV processor, eliminating duplication.

        :param data: Data dictionary where outer keys are column headers (time periods),
            inner keys are rows (categories), values are amounts
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Formatted string (HTML, CSV, or plain text)

        Example::

            >>> data = {"Total": {"Grocery": 150.5}}
            >>> # HTML output
            >>> html = service.format_for_output(data, output_format="html")
            >>> # CSV to file
            >>> csv = service.format_for_output(data, output_file="output.csv")
            >>> # Console string
            >>> text = service.format_for_output(data)
        """
        if output_format == 'html':
            return self.format_as_html_table(
                data,
                nowrap=nowrap
            )
        elif output_file:
            # Save to file and return CSV
            csv = self.format_as_csv(
                data,
                delimiter=';'
            )
            with open(output_file, 'w') as f:
                f.write(csv)
            return csv
        else:
            return self.format_as_string(
                data,
                nowrap=nowrap
            )

    def format_datatables_as_html_table(
        self,
        dt_responses: Dict[str, AccountResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format AccountResponse as HTML table.

        Extracts summary data from AccountResponse and formats as HTML.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :return: HTML string with formatted table
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data: SummaryData = SummaryData.from_datatable_response(
            dt_response=dt_responses[selected_account_id],
            account_id=selected_account_id,
            include_calculated=True  # Include Balance and Total Spendings rows
        )

        return self.format_as_html_table(
            data=summary_data.summary,
            nowrap=nowrap
        )

    def format_datatables_as_csv(
        self,
        dt_responses: Dict[str, AccountResponse],
        account_id: Optional[str] = None,
        delimiter: str = ',',
    ) -> str:
        """Format AccountResponse as CSV string.

        Extracts summary data from AccountResponse and formats as CSV.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param delimiter: CSV delimiter character
        :return: CSV formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data: SummaryData = SummaryData.from_datatable_response(
            dt_response=dt_responses[selected_account_id],
            account_id=selected_account_id,
            include_calculated=False
        )

        return self.format_as_csv(
            data=summary_data.summary,
            delimiter=delimiter
        )

    def format_datatables_as_string(
        self,
        dt_responses: Dict[str, AccountResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False,
    ) -> str:
        """Format AccountResponse as plain string for console output.

        Extracts summary data from AccountResponse and formats as plain text.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Plain text formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account (include Balance and Total Spendings)
        summary_data: SummaryData = SummaryData.from_datatable_response(
            dt_response=dt_responses[selected_account_id],
            account_id=selected_account_id,
            include_calculated=True  # Include Balance and Total Spendings rows
        )

        return self.format_as_string(
            data=summary_data.summary,
            nowrap=nowrap,
        )

    def format_datatables_for_output(
        self,
        dt_responses: Dict[str, AccountResponse],
        account_id: Optional[str] = None,
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format AccountResponse for various output types.

        This is a convenience method for formatting AccountResponse to
        HTML, CSV file, or console string.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Formatted string (HTML, CSV, or plain text)
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account (include Balance and Total Spendings)
        summary_data: SummaryData = SummaryData.from_datatable_response(
            dt_response=dt_responses[selected_account_id],
            account_id=selected_account_id,
            include_calculated=True  # Include Balance and Total Spendings rows
        )

        return self.format_for_output(
            data=summary_data.summary,
            output_format=output_format,
            output_file=output_file,
            nowrap=nowrap
        )

    def format_all_accounts_for_output(
        self,
        dt_responses: Dict[str, AccountResponse],
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format all accounts for output using existing formatters.

        Handles multi-account iteration internally, calling the appropriate
        existing formatter for each account and combining results with separators.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Formatted string with all accounts
        """
        if not dt_responses:
            return ""

        outputs = []
        has_multiple_accounts = len(dt_responses) > 1

        for account_id in sorted(dt_responses.keys()):
            # Add account header for multi-account scenarios
            if has_multiple_accounts:
                # Format account number (add dash every 8 digits)
                formatted_id = self.format_account_id(account_id)
                separator = "=" * 60
                header = f"\n{separator}\n{_('Account')}: {formatted_id}\n{separator}\n"
                outputs.append(header)

            # Use existing formatter for single account
            output = self.format_datatables_for_output(
                dt_responses=dt_responses,
                account_id=account_id,
                output_format=output_format,
                output_file=None,  # Handle file writing at end
                nowrap=nowrap
            )
            outputs.append(output)

        # Combine all outputs
        result = '\n\n'.join(outputs) if has_multiple_accounts else outputs[0]

        # Handle file output once at the end
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)

        return result

    def _convert_metadata_to_highlights_dict(self, statistical_metadata: 'StatisticalMetadata') -> Dict[str, List[str]]:
        """Convert StatisticalMetadata to the highlights dict format expected by templates.

        :param statistical_metadata: StatisticalMetadata containing CellHighlight objects
        :return: Dictionary of highlights keyed by row_id, with list of highlight types
        """
        highlights_dict: Dict[str, List[str]] = {}
        for highlight in statistical_metadata.highlights:
            if highlight.row_id not in highlights_dict:
                highlights_dict[highlight.row_id] = []
            highlights_dict[highlight.row_id].extend(highlight.highlight_types)
        return highlights_dict

    def prepare_accounts_for_template(
        self,
        dt_responses: Dict[str, AccountResponse],
        statistical_metadata: StatisticalMetadata
    ) -> Dict[str, Any]:
        """Prepare accounts data for Jinja2 template rendering.

        Provides structured data that templates can iterate over, including
        formatted account identifiers and metadata. Templates can still access
        the underlying AccountResponse for detailed rendering.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param statistical_metadata: StatisticalMetadata containing highlights for all accounts
        :return: Dict with 'accounts' list, 'highlights' (combined), and 'has_multiple_accounts' flag
        """
        accounts = []
        all_highlights_combined = self._convert_metadata_to_highlights_dict(statistical_metadata)

        for account_id in sorted(dt_responses.keys()):
            dt_response = dt_responses[account_id]

            # Format account number (add dash every 8 digits)
            formatted_id = '-'.join(
                account_id[i:i+8]
                for i in range(0, len(account_id), 8)
            )

            # Filter highlights to only include those that belong to this account
            # This prevents JSON serialization errors by ensuring all row_ids exist in current account
            existing_row_ids = {row.row_id for row in dt_response.data}
            filtered_highlights = {}
            for row_id, highlight_types in all_highlights_combined.items():
                if row_id in existing_row_ids:
                    filtered_highlights[row_id] = highlight_types

            accounts.append({
                'id': account_id,
                'formatted_id': formatted_id,
                'currency': dt_response.currency,
                'dt_response': dt_response,
                'highlights': filtered_highlights,
            })

        return {
            'accounts': accounts,
            'highlights': all_highlights_combined,  # Combined highlights for all accounts
            'has_multiple_accounts': len(accounts) > 1
        }

    def _select_account(
        self,
        dt_responses: Dict[str, AccountResponse],
        account_id: Optional[str] = None
    ) -> str:
        """Select and validate account from AccountResponse dict.

        :param dt_responses: Dict mapping account_id to AccountResponse
        :param account_id: Optional account ID to select. If None and multiple accounts
            exist, raises ValueError. If None and single account exists, uses that account.
        :return: Selected account_id
        :raises ValueError: If multiple accounts exist but no account_id specified,
            or if specified account_id not found
        """
        if not dt_responses:
            raise ValueError("No account data available")

        # If account_id not specified, validate single account
        if account_id is None:
            if len(dt_responses) > 1:
                available_accounts = ', '.join(dt_responses.keys())
                raise ValueError(
                    f"Multiple accounts found ({len(dt_responses)}) but no account_id specified. "
                    f"Available accounts: {available_accounts}. "
                    f"Please specify account_id parameter."
                )
            # Single account - use it
            account_id = next(iter(dt_responses.keys()))

        # Validate account_id exists
        if account_id not in dt_responses:
            available_accounts = ', '.join(dt_responses.keys())
            raise ValueError(
                f"Account '{account_id}' not found in responses. "
                f"Available accounts: {available_accounts}"
            )

        return account_id

    # Response Building Methods (from ResponseBuilderService)

    def build_api_detailed_response(
        self,
        account_response: Dict[str, AccountResponse],
        metadata: Dict[str, Any] | ProcessingMetadata,
        params: ProcessingRequest,
        processing_time: float,
        result_id: str
    ) -> DetailedResponse:
        """Build standardized API detailed response.

        Args:
            account_response: Dict[str, AccountResponse] mapping account to response objects
            metadata: Processing metadata (row_count, etc.)
            params: Request parameters
            processing_time: Total processing time in seconds

        Returns:
            DetailedResponse: Pydantic model for v2 API response with array of account responses

        Example:
            >>> response = service.build_api_detailed_response(
            ...     account_response={'12345': dt_response1, '67890': dt_response2},
            ...     metadata={'row_count': 150},
            ...     params=ProcessingRequest(ml_enabled=True),
            ...     processing_time=1.2
            ... )
        """
        # Convert dict to array, sorted by account ID
        aggregated_rows = []
        for account_id in sorted(account_response.keys()):
            dt_response = account_response[account_id]
            # Add all aggregated rows from this account
            aggregated_rows.extend(dt_response.data)

        # Handle both ProcessingMetadata object and dict for backward compatibility
        if isinstance(metadata, dict):
            row_count = metadata.get('row_count', 0)
        else:
            # Assume it's a ProcessingMetadata object
            row_count = metadata.row_count

        return DetailedResponse(
            data=aggregated_rows,  # List[AggregatedRow] from all accounts
            metadata=ProcessingMetadata(
                row_count=row_count,
                processing_time=processing_time,
                ml_enabled=params.ml_enabled,
                result_id=result_id,
                date_range=self._build_date_range(params)
            )
        )

    def build_error_response(
        self,
        error: Exception,
        default_code: int = 500,
        default_message: str = "Internal server error",
        context: Optional[Dict[str, Any]] = None
    ) -> tuple["Response", int]:
        """Build standardized error response.

        Centralizes error response building logic that was duplicated in
        api/helpers.py::handle_error() and api/error_handlers.py.

        Args:
            error: The exception to handle
            default_code: Default status code if exception type not recognized
            default_message: Default error message
            context: Optional additional context

        Returns:
            tuple: (jsonified error response, status code)

        Example:
            >>> response, code = service.build_error_response(
            ...     ValueError("Invalid date format"),
            ...     default_code=422,
            ...     default_message="Validation error"
            ... )
        """
        from flask import jsonify
        from werkzeug.exceptions import BadRequest
        from pydantic import ValidationError as PydanticValidationError
        from whatsthedamage.utils.validation import ValidationError

        # Log the error with context before building response
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "status_code": default_code
        }
        if context:
            error_context.update(context)

        self.logger.error("Building error response", extra={"context": error_context})

        # Determine status code and message based on exception type
        if isinstance(error, BadRequest):
            field_value = context.get("field", "unknown") if context else "unknown"
            error_response = ErrorResponse(
                code=400,
                message=str(error),
                details={"field": str(field_value)}
            )
            status_code = 400

        elif isinstance(error, PydanticValidationError):
            validation_errors = [str(err) for err in error.errors()]
            error_response = ErrorResponse(
                code=400,
                message="Invalid request parameters",
                details={"errors": validation_errors}
            )
            status_code = 400

        elif isinstance(error, ValidationError):
            error_response = ErrorResponse(
                code=400,
                message=error.result.error_message or "Validation failed",
                details=error.result.details or {}
            )
            status_code = 400

        elif isinstance(error, FileNotFoundError):
            error_response = ErrorResponse(
                code=400,
                message="File not found",
                details={"error": str(error)}
            )
            status_code = 400

        elif isinstance(error, ValueError):
            error_response = ErrorResponse(
                code=422,
                message="Processing error",
                details={"error": str(error)}
            )
            status_code = 422

        else:
            # Generic exception handling
            error_response = ErrorResponse(
                code=default_code,
                message=default_message,
                details={"error": str(error), "type": type(error).__name__}
            )
            status_code = default_code

        return jsonify(error_response.model_dump()), status_code

    def format_processing_response_for_frontend(
        self,
        cached_result: ProcessingResponse | None
    ) -> ResultsApiResponse:
        """Convert cached ProcessingResponse to frontend-expected format.

        Extracts account data, highlights, and drilldown URLs from a cached
        ProcessingResponse and formats it for the Vue frontend.

        Args:
            cached_result: Cached ProcessingResponse from cache service

        Returns:
            ResultsApiResponse: Typed response for /api/v2/results/<id> endpoint

        Raises:
            ValueError: If cached_result is None

        Note:
            This consolidates the data transformation logic that was previously
            duplicated in api/v2/endpoints.py get_results() endpoint.
        """
        if cached_result is None:
            raise ValueError('Result data not found or expired')

        highlights_dict = self._convert_highlights(cached_result)
        accounts_list, drilldown_urls_dict = self._build_accounts_and_drilldowns(
            cached_result
        )

        # Build final response
        return ResultsApiResponse(
            result_id=cached_result.result_id,
            accounts_data=AccountsDataResponse(
                accounts=accounts_list,
                highlights=highlights_dict
            ),
            drilldown_urls_by_account=drilldown_urls_dict
        )

    def _convert_highlights(
        self, cached_result: ProcessingResponse
    ) -> Dict[str, Any]:
        """Convert highlights from cached result metadata."""
        if hasattr(cached_result, 'statistical_metadata'):
            return self._convert_metadata_to_highlights_dict(cached_result.statistical_metadata)
        return {}

    def _build_accounts_and_drilldowns(
        self, cached_result: ProcessingResponse
    ) -> tuple[List[AccountDataResponse], Dict[str, DrilldownUrls]]:
        """Build accounts list and drilldown URLs from cached result data."""
        accounts_list: List[AccountDataResponse] = []
        drilldown_urls_dict: Dict[str, DrilldownUrls] = {}

        if not hasattr(cached_result, 'data') or not isinstance(cached_result.data, dict):
            return accounts_list, drilldown_urls_dict

        for account_id, account_data in cached_result.data.items():
            account_name = self._get_account_name(account_id, account_data)
            dt_response_data = self._convert_account_data_to_frontend(account_data)

            accounts_list.append(AccountDataResponse(
                id=account_id,
                name=account_name,
                dt_response={'data': dt_response_data}
            ))

            drilldown_urls = self._generate_drilldown_urls(
                cached_result.result_id, account_id, account_data, dt_response_data
            )
            drilldown_urls_dict[account_id] = drilldown_urls

        return accounts_list, drilldown_urls_dict

    def _get_account_name(self, account_id: str, account_data: Any) -> str:
        """Get account name with fallback logic."""
        account_name = getattr(account_data, 'name', None)
        if not account_name and hasattr(account_data, 'account'):
            account_name = account_data.account or f'Account {account_id}'
        if not account_name:
            account_name = f'Account {account_id}'
        return account_name

    def _convert_account_data_to_frontend(self, account_data: Any) -> List[Dict[str, Any]]:
        """Convert account data rows to frontend format."""
        dt_response_data: List[Dict[str, Any]] = []

        if not hasattr(account_data, 'data'):
            return dt_response_data

        for row in account_data.data:
            details_array = self._convert_row_details(row)

            dt_response_data.append({
                'category_id': row.category_id,
                'date': {'display': row.date.display, 'timestamp': row.date.timestamp},
                'total': {'display': row.total.display, 'raw': row.total.raw},
                'details': details_array,
                'row_id': row.row_id
            })

        return dt_response_data

    def _convert_row_details(self, row: Any) -> List[Dict[str, Any]]:
        """Convert row details to frontend format."""
        details_array: List[Dict[str, Any]] = []

        if hasattr(row, 'details') and row.details:
            for detail in row.details:
                details_array.append({
                    'date': {'display': detail.date.display},
                    'amount': {'display': detail.amount.display},
                    'merchant': detail.merchant,
                    'currency': detail.currency if hasattr(detail, 'currency') else '',
                    'type': detail.type if hasattr(detail, 'type') else '',
                    'confidence': detail.confidence if hasattr(detail, 'confidence') else None,
                    'notice': detail.notice if hasattr(detail, 'notice') else None,
                    'row_id': detail.row_id if hasattr(detail, 'row_id') else ''
                })

        return details_array

    def _generate_drilldown_urls(
        self,
        result_id: str,
        account_id: str,
        account_data: Any,
        dt_response_data: List[Dict[str, Any]]
    ) -> DrilldownUrls:
        """Generate drilldown URLs for an account, using service if available."""
        category_urls: Dict[str, DrilldownUrlInfo] = {}
        month_urls: Dict[str, MonthUrlInfo] = {}
        cell_urls: Dict[str, CellUrlInfo] = {}

        drilldown_urls_generated = self._generate_drilldown_urls_with_service(
            result_id, account_id, account_data, category_urls, month_urls, cell_urls
        )

        if not drilldown_urls_generated:
            self._generate_drilldown_urls_fallback(
                result_id, account_id, dt_response_data,
                category_urls, month_urls, cell_urls
            )

        return DrilldownUrls(
            account_id=account_id,
            category_urls=category_urls,
            month_urls=month_urls,
            cell_urls=cell_urls
        )

    def _generate_drilldown_urls_with_service(
        self,
        result_id: str,
        account_id: str,
        account_data: Any,
        category_urls: Dict[str, DrilldownUrlInfo],
        month_urls: Dict[str, MonthUrlInfo],
        cell_urls: Dict[str, CellUrlInfo]
    ) -> bool:
        """Try to generate drilldown URLs using DrilldownResponseService."""
        try:
            from flask import current_app
            if not hasattr(current_app, 'extensions'):
                return False

            drilldown_response_service = current_app.extensions.get('drilldown_response_service')
            if not drilldown_response_service:
                return False

            account_drilldown_urls = drilldown_response_service.generate_drilldown_urls(
                result_id, account_id, account_data
            )

            # Convert dict URLs to DTOs
            for cat, cat_info in account_drilldown_urls.get('category_urls', {}).items():
                category_urls[cat] = DrilldownUrlInfo(**cat_info)
            for month, month_info in account_drilldown_urls.get('month_urls', {}).items():
                month_urls[month] = MonthUrlInfo(**month_info)
            for cell, cell_info in account_drilldown_urls.get('cell_urls', {}).items():
                cell_urls[cell] = CellUrlInfo(**cell_info)

            return True
        except (RuntimeError, ImportError):
            # current_app not available or service not registered - will use fallback
            return False

    def _generate_drilldown_urls_fallback(
        self,
        result_id: str,
        account_id: str,
        dt_response_data: List[Dict[str, Any]],
        category_urls: Dict[str, DrilldownUrlInfo],
        month_urls: Dict[str, MonthUrlInfo],
        cell_urls: Dict[str, CellUrlInfo]
    ) -> None:
        """Generate fallback drilldown URLs when service is not available."""
        for row_data in dt_response_data:
            category = str(row_data.get('category', ''))
            month_ts = str(row_data.get('date', {}).get('timestamp', ''))
            row_id = str(row_data.get('row_id', ''))

            if category and category not in category_urls:
                category_urls[category] = DrilldownUrlInfo(
                    category_url=f"/results/{result_id}/accounts/{account_id}/categories/{category}/months",
                    category_id=category
                )

            if month_ts and month_ts not in month_urls:
                month_urls[month_ts] = MonthUrlInfo(
                    month_url=f"/results/{result_id}/accounts/{account_id}/months/{month_ts}/categories",
                    month_id=month_ts
                )

            if row_id and category and month_ts:
                cell_urls[row_id] = CellUrlInfo(
                    cell_url=f"/results/{result_id}/accounts/{account_id}/categories/{category}/months/{month_ts}/transactions",
                    category_id=category,
                    month_id=month_ts
                )

    # Private helper methods

    def _build_date_range(self, params: ProcessingRequest) -> Optional[Dict[str, str]]:
        """Build date range dictionary from parameters.

        Args:
            params: Processing request parameters

        Returns:
            Dict with start/end dates or None if no dates specified
        """
        if not params.start_date and not params.end_date:
            return None

        date_range = {}
        if params.start_date:
            date_range['start'] = params.start_date
        if params.end_date:
            date_range['end'] = params.end_date

        return date_range