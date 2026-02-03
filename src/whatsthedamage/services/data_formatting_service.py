"""Data Formatting Service for standardized data output formatting.

This service centralizes all data formatting logic across web, API, and CLI,
consolidating logic from DataFrameFormatter and various formatting
scattered in controllers.

Architecture Patterns:
- Strategy Pattern: Different formatting strategies per output type
- Adapter Pattern: Adapt DataFrame to various output formats
- Factory Pattern: Create appropriate formatter based on output type
- Decorator Pattern: Add features (sorting, currency) to base formatters
- DRY Principle: Single implementation for formatting operations
"""
import pandas as pd
import json
from typing import Dict, Optional, Any
from whatsthedamage.models.dt_models import DataTablesResponse, StatisticalMetadata, SummaryData
from gettext import gettext as _
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService


class DataFormattingService:
    """Service for formatting data into various output formats.

    Supports multiple output formats:
    - HTML tables (with optional sorting metadata)
    - CSV strings
    - JSON strings
    - Currency formatting

    Account aware.
    """

    def __init__(self, statistical_analysis_service: Optional[StatisticalAnalysisService] = None) -> None:
        """Initialize the data formatting service."""
        self.statistical_analysis_service = statistical_analysis_service
        self._categories_header = _("Categories")


    @staticmethod
    def format_account_id(account_id: str) -> str:
        """Format account ID by adding dashes every 8 digits.

        This utility method provides consistent account ID formatting across
        all interfaces (CLI, Web, API).

        :param account_id: Raw account ID string
        :return: Formatted account ID with dashes every 8 digits
        """
        formatted_id = '-'.join(
                    account_id[i:i+8]
                    for i in range(0, len(account_id), 8)
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
        :param currency: Currency code (e.g., "EUR", "USD")
        :param nowrap: If True, disables text wrapping in pandas output
        :return: HTML string with formatted table

        Example::

            >>> data = {"Total": {"Grocery": 150.5, "Utilities": 80.0}}
            >>> html = service.format_as_html_table(data, "EUR")
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
        :param currency: Currency code (e.g., "EUR", "USD")
        :param delimiter: CSV delimiter character
        :return: CSV formatted string

        Example::

            >>> data = {"January": {"Grocery": 150.5}}
            >>> csv = service.format_as_csv(data, "EUR")
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
        :param currency: Currency code (e.g., "EUR", "USD")
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Plain text formatted string

        Example::

            >>> data = {"Total": {"Grocery": 150.5}}
            >>> text = service.format_as_string(data, "EUR")
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
        :param currency: Currency code (e.g., "EUR", "USD")
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Formatted string (HTML, CSV, or plain text)

        Example::

            >>> data = {"Total": {"Grocery": 150.5}}
            >>> # HTML output
            >>> html = service.format_for_output(data, "EUR", output_format="html")
            >>> # CSV to file
            >>> csv = service.format_for_output(data, "EUR", output_file="output.csv")
            >>> # Console string
            >>> text = service.format_for_output(data, "EUR")
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
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format DataTablesResponse as HTML table.

        Extracts summary data from DataTablesResponse and formats as HTML.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :return: HTML string with formatted table
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data: SummaryData = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_html_table(
            data=summary_data.summary,
            nowrap=nowrap
        )

    def format_datatables_as_csv(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        delimiter: str = ',',
    ) -> str:
        """Format DataTablesResponse as CSV string.

        Extracts summary data from DataTablesResponse and formats as CSV.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param delimiter: CSV delimiter character
        :return: CSV formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data: SummaryData = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_csv(
            data=summary_data.summary,
            delimiter=delimiter
        )

    def format_datatables_as_string(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False,
    ) -> str:
        """Format DataTablesResponse as plain string for console output.

        Extracts summary data from DataTablesResponse and formats as plain text.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :return: Plain text formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data: SummaryData = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_string(
            data=summary_data.summary,
            nowrap=nowrap,
        )

    def format_datatables_for_output(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format DataTablesResponse for various output types.

        This is a convenience method for formatting DataTablesResponse to
        HTML, CSV file, or console string.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
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

        # Extract summary for selected account
        summary_data: SummaryData = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_for_output(
            data=summary_data.summary,
            output_format=output_format,
            output_file=output_file,
            nowrap=nowrap
        )

    def format_all_accounts_for_output(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False
    ) -> str:
        """Format all accounts for output using existing formatters.

        Handles multi-account iteration internally, calling the appropriate
        existing formatter for each account and combining results with separators.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
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

    def _convert_metadata_to_highlights_dict(self, metadata: 'StatisticalMetadata') -> Dict[str, str]:
        """Convert StatisticalMetadata to the highlights dict format expected by templates.

        :param metadata: StatisticalMetadata containing CellHighlight objects
        :return: Dictionary of highlights keyed by row_id
        """
        highlights_dict = {}
        for highlight in metadata.highlights:
            highlights_dict[highlight.row_id] = highlight.highlight_type
        return highlights_dict

    def prepare_accounts_for_template(
        self,
        dt_responses: Dict[str, DataTablesResponse]
    ) -> Dict[str, Any]:
        """Prepare accounts data for Jinja2 template rendering.

        Provides structured data that templates can iterate over, including
        formatted account identifiers and metadata. Templates can still access
        the underlying DataTablesResponse for detailed rendering.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :return: Dict with 'accounts' list and 'has_multiple_accounts' flag
        """
        accounts = []

        for account_id in sorted(dt_responses.keys()):
            dt_response = dt_responses[account_id]

            # Format account number (add dash every 8 digits)
            formatted_id = '-'.join(
                account_id[i:i+8]
                for i in range(0, len(account_id), 8)
            )

            # Use cached statistical metadata (attached by ProcessingService)
            statistical_metadata = dt_response.statistical_metadata
            if statistical_metadata is None:
                raise ValueError("Statistical metadata not found. This should be attached by ProcessingService.")
            highlights = self._convert_metadata_to_highlights_dict(statistical_metadata)

            accounts.append({
                'id': account_id,
                'formatted_id': formatted_id,
                'currency': dt_response.currency,
                'dt_response': dt_response,
                'highlights': highlights,
            })

        return {
            'accounts': accounts,
            'has_multiple_accounts': len(accounts) > 1
        }

    def _select_account(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None
    ) -> str:
        """Select and validate account from DataTablesResponse dict.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
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

    def _extract_summary_from_account(
        self,
        dt_response: DataTablesResponse,
        account_id: str,
        include_calculated: bool = False
    ) -> SummaryData:
        """Extract summary data from a single account's DataTablesResponse.

        This method extracts and caches summary data from a DataTablesResponse for
        a single account. Results are cached by account_id to avoid repeated extraction.

        :param dt_response: DataTablesResponse for a single account
        :param account_id: Account identifier for caching
        :param include_calculated: Whether to include calculated rows in summary (for statistical analysis)
        :return: SummaryData with extracted summary, currency, and account_id

        Example::

            >>> dt_response = DataTablesResponse(...)
            >>> summary_data = service._extract_summary_from_account(dt_response, '12345')
            >>> assert summary_data.account_id == '12345'
            >>> assert summary_data.currency == 'EUR'
        """
        # Aggregate by canonical timestamp first. This keeps year information
        # unambiguous and simplifies merging category totals.
        # period_map: timestamp -> { 'display': str (column header), 'categories': {category: amount} }
        period_map: Dict[int, Dict[str, Any]] = {}

        for agg_row in dt_response.data:
            # Skip calculated rows if requested (for statistical analysis)
            if not include_calculated and getattr(agg_row, 'is_calculated', False):
                continue

            period_field = agg_row.date

            ts = period_field.timestamp
            display = period_field.display

            if ts not in period_map:
                period_map[ts] = {'display': display, 'categories': {}}

            cats = period_map[ts]['categories']
            cats[agg_row.category] = cats.get(agg_row.category, 0.0) + float(agg_row.total.raw)

        # If multiple timestamps share the same display (e.g., 'January' across different years),
        # append the timestamp to disambiguate. This creates unique column headers like
        # 'January (1704067200)'. Otherwise use the human-readable display as the column header.
        display_counts: Dict[str, int] = {}
        for v in period_map.values():
            display_counts[v['display']] = display_counts.get(v['display'], 0) + 1

        summary = {}
        # Iterate periods in descending timestamp order (most recent first)
        for ts in sorted(period_map.keys(), reverse=True):
            display = period_map[ts]['display']
            column_header = display if display_counts.get(display, 0) == 1 else f"{display} ({ts})"
            summary[column_header] = period_map[ts]['categories']

        summary_data = SummaryData(
            summary=summary,
            currency=dt_response.currency,
            account_id=account_id
        )

        return summary_data
