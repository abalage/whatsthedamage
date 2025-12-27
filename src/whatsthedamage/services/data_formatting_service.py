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
from typing import Dict, List, Tuple, Union, Optional, Any
from pydantic import BaseModel
from whatsthedamage.config.dt_models import DataTablesResponse
from gettext import gettext as _


class SummaryData(BaseModel):
    """Extracted summary data from a DataTablesResponse for a single account.

    This model encapsulates the summary data extracted from transaction data,
    providing a simplified format for formatting and display.

    Attributes:
        summary: Dict mapping month names to category amounts
            Format: {month_name: {category: amount}}
        currency: Currency code (e.g., 'EUR', 'USD')
        account_id: Account identifier this summary belongs to
    """
    summary: Dict[str, Dict[str, float]]
    currency: str
    account_id: str

    class Config:
        frozen = True  # Immutable for safe caching


class DataFormattingService:
    """Service for formatting data into various output formats.

    Supports multiple output formats:
    - HTML tables (with optional sorting metadata)
    - CSV strings
    - JSON strings
    - Currency formatting

    Account aware.
    """

    def __init__(self) -> None:
        """Initialize the data formatting service."""
        self._summary_cache: Dict[str, SummaryData] = {}  # Cache by account_id

    def format_as_html_table(
        self,
        data: Dict[str, Dict[str, float]],
        currency: str,
        nowrap: bool = False,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> str:
        """Format data as HTML table with optional sorting.

        :param data: Data dictionary where outer keys are columns (months),
            inner keys are rows (categories), values are amounts
        :param currency: Currency code (e.g., "EUR", "USD")
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
        :return: HTML string with formatted table

        Example::

            >>> data = {"Total": {"Grocery": 150.5, "Utilities": 80.0}}
            >>> html = service.format_as_html_table(data, "EUR")
            >>> assert "150.50 EUR" in html
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

        # Format with currency if enabled
        if not no_currency_format:
            df = df.apply(
                lambda row: row.apply(
                    lambda value: f"{value:.2f} {currency}" if isinstance(value, (int, float)) else value
                ),
                axis=1
            )

        # Convert to HTML
        html = df.to_html(border=0)

        # Replace empty header with categories header
        html = html.replace('<th></th>', f'<th>{categories_header}</th>', 1)

        return html

    def format_as_csv(
        self,
        data: Dict[str, Dict[str, float]],
        currency: str,
        delimiter: str = ',',
        no_currency_format: bool = False
    ) -> str:
        """Format data as CSV string.

        :param data: Data dictionary where outer keys are columns (months),
            inner keys are rows (categories), values are amounts
        :param currency: Currency code (e.g., "EUR", "USD")
        :param delimiter: CSV delimiter character
        :param no_currency_format: If True, disables currency formatting
        :return: CSV formatted string

        Example::

            >>> data = {"January": {"Grocery": 150.5}}
            >>> csv = service.format_as_csv(data, "EUR")
            >>> assert "Grocery,150.50 EUR" in csv
        """
        # Create DataFrame
        df = pd.DataFrame(data)
        df = df.fillna(0)
        df = df.sort_index()

        # Format with currency if enabled
        if not no_currency_format:
            df = df.apply(
                lambda row: row.apply(
                    lambda value: f"{value:.2f} {currency}" if isinstance(value, (int, float)) else value
                ),
                axis=1
            )

        # Convert to CSV string
        return df.to_csv(sep=delimiter)

    def format_as_string(
        self,
        data: Dict[str, Dict[str, float]],
        currency: str,
        nowrap: bool = False,
        no_currency_format: bool = False
    ) -> str:
        """Format data as plain string for console output.

        :param data: Data dictionary where outer keys are columns (months),
            inner keys are rows (categories), values are amounts
        :param currency: Currency code (e.g., "EUR", "USD")
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :return: Plain text formatted string

        Example::

            >>> data = {"Total": {"Grocery": 150.5}}
            >>> text = service.format_as_string(data, "EUR")
            >>> assert "Grocery" in text and "150.50 EUR" in text
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

        # Format with currency if enabled
        if not no_currency_format:
            df = df.apply(
                lambda row: row.apply(
                    lambda value: f"{value:.2f} {currency}" if isinstance(value, (int, float)) else value
                ),
                axis=1
            )

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

    def prepare_summary_table_data(
        self,
        data: Dict[str, Dict[str, float]],
        currency: str,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> Tuple[List[str], List[List[Dict[str, Union[str, float, None]]]]]:
        """Prepare summary table data with display/order metadata for rendering.

        Converts summary data directly to structured format with display values
        and sorting metadata, without going through HTML parsing. This is the
        proper way to enhance data before rendering.

        :param data: Data dictionary where outer keys are columns (months),
            inner keys are rows (categories), values are amounts
        :param currency: Currency code (e.g., "EUR", "USD")
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
        :return: Tuple of (headers, enhanced_rows) where headers is a list of
            column header strings and enhanced_rows is a list of rows, each row
            is a list of dicts with 'display' and 'order' keys

        Example::

            >>> data = {"January": {"Grocery": 150.5, "Utilities": 80.0}}
            >>> headers, rows = service.prepare_summary_table_data(data, "EUR")
            >>> assert headers == ["Categories", "January"]
            >>> assert rows[0][0]['display'] == "Grocery"
            >>> assert rows[0][1]['display'] == "150.50 EUR"
            >>> assert rows[0][1]['order'] == 150.5
        """
        # Create DataFrame from data
        df = pd.DataFrame(data)
        df = df.fillna(0)
        df = df.sort_index()

        # Build headers: Categories + month columns
        headers = [categories_header] + list(df.columns)

        # Build enhanced rows with display/order metadata
        enhanced_rows: List[List[Dict[str, Union[str, float, None]]]] = []

        for category in df.index:
            row: List[Dict[str, Union[str, float, None]]] = []

            # First cell: category name (no sorting order)
            row.append({
                'display': str(category),
                'order': None
            })

            # Remaining cells: numeric values with display and order
            for column in df.columns:
                value = df.loc[category, column]

                # Convert to float for consistent handling
                # Type ignore needed for pandas Scalar type compatibility
                numeric_value = float(value) if pd.notna(value) else 0.0  # type: ignore[arg-type]

                # Format display value
                if no_currency_format:
                    display_value = f"{numeric_value:.2f}"
                else:
                    display_value = f"{numeric_value:.2f} {currency}"

                # Add cell with display and order values
                row.append({
                    'display': display_value,
                    'order': numeric_value
                })

            enhanced_rows.append(row)

        return headers, enhanced_rows

    def format_for_output(
        self,
        data: Dict[str, Dict[str, float]],
        currency: str,
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> str:
        """Format data for various output types (HTML, CSV file, or console string).

        This is a convenience method that consolidates the common formatting logic
        used across CLI and CSV processor, eliminating duplication.

        :param data: Data dictionary where outer keys are columns (months),
            inner keys are rows (categories), values are amounts
        :param currency: Currency code (e.g., "EUR", "USD")
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
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
                currency=currency,
                nowrap=nowrap,
                no_currency_format=no_currency_format,
                categories_header=categories_header
            )
        elif output_file:
            # Save to file and return CSV
            csv = self.format_as_csv(
                data,
                currency=currency,
                delimiter=';',
                no_currency_format=no_currency_format
            )
            with open(output_file, 'w') as f:
                f.write(csv)
            return csv
        else:
            return self.format_as_string(
                data,
                currency=currency,
                nowrap=nowrap,
                no_currency_format=no_currency_format
            )

    def format_datatables_as_html_table(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> str:
        """Format DataTablesResponse as HTML table.

        Extracts summary data from DataTablesResponse and formats as HTML.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
        :return: HTML string with formatted table
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_html_table(
            data=summary_data.summary,
            currency=summary_data.currency,
            nowrap=nowrap,
            no_currency_format=no_currency_format,
            categories_header=categories_header
        )

    def format_datatables_as_csv(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        delimiter: str = ',',
        no_currency_format: bool = False
    ) -> str:
        """Format DataTablesResponse as CSV string.

        Extracts summary data from DataTablesResponse and formats as CSV.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param delimiter: CSV delimiter character
        :param no_currency_format: If True, disables currency formatting
        :return: CSV formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_csv(
            data=summary_data.summary,
            currency=summary_data.currency,
            delimiter=delimiter,
            no_currency_format=no_currency_format
        )

    def format_datatables_as_string(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        nowrap: bool = False,
        no_currency_format: bool = False
    ) -> str:
        """Format DataTablesResponse as plain string for console output.

        Extracts summary data from DataTablesResponse and formats as plain text.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :return: Plain text formatted string
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_as_string(
            data=summary_data.summary,
            currency=summary_data.currency,
            nowrap=nowrap,
            no_currency_format=no_currency_format
        )

    def prepare_datatables_summary_table_data(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> Tuple[List[str], List[List[Dict[str, Union[str, float, None]]]]]:
        """Prepare summary table data from DataTablesResponse with display/order metadata.

        Extracts summary data from DataTablesResponse and prepares for rendering.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param account_id: Account ID to format. If None and multiple accounts exist,
            raises ValueError. If None and single account exists, uses that account.
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
        :return: Tuple of (headers, enhanced_rows)
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.prepare_summary_table_data(
            data=summary_data.summary,
            currency=summary_data.currency,
            no_currency_format=no_currency_format,
            categories_header=categories_header
        )

    def format_datatables_for_output(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        account_id: Optional[str] = None,
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
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
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
        :return: Formatted string (HTML, CSV, or plain text)
        :raises ValueError: If multiple accounts exist but no account_id specified
        """
        # Select and validate account
        selected_account_id = self._select_account(dt_responses, account_id)

        # Extract summary for selected account
        summary_data = self._extract_summary_from_account(
            dt_responses[selected_account_id],
            selected_account_id
        )

        return self.format_for_output(
            data=summary_data.summary,
            currency=summary_data.currency,
            output_format=output_format,
            output_file=output_file,
            nowrap=nowrap,
            no_currency_format=no_currency_format,
            categories_header=categories_header
        )

    def format_all_accounts_for_output(
        self,
        dt_responses: Dict[str, DataTablesResponse],
        output_format: Optional[str] = None,
        output_file: Optional[str] = None,
        nowrap: bool = False,
        no_currency_format: bool = False,
        categories_header: str = "Categories"
    ) -> str:
        """Format all accounts for output using existing formatters.

        Handles multi-account iteration internally, calling the appropriate
        existing formatter for each account and combining results with separators.

        :param dt_responses: Dict mapping account_id to DataTablesResponse
        :param output_format: Output format ('html' or None for default)
        :param output_file: Path to output file (triggers CSV export)
        :param nowrap: If True, disables text wrapping in pandas output
        :param no_currency_format: If True, disables currency formatting
        :param categories_header: Header text for the categories column
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
                formatted_id = '-'.join(
                    account_id[i:i+8]
                    for i in range(0, len(account_id), 8)
                )
                separator = "=" * 60
                header = f"\n{separator}\n{_('Account')}: {formatted_id}\n{separator}\n"
                outputs.append(header)

            # Use existing formatter for single account
            output = self.format_datatables_for_output(
                dt_responses=dt_responses,
                account_id=account_id,
                output_format=output_format,
                output_file=None,  # Handle file writing at end
                nowrap=nowrap,
                no_currency_format=no_currency_format,
                categories_header=categories_header
            )
            outputs.append(output)

        # Combine all outputs
        result = '\n\n'.join(outputs) if has_multiple_accounts else outputs[0]

        # Handle file output once at the end
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)

        return result

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

            accounts.append({
                'id': account_id,
                'formatted_id': formatted_id,
                'currency': dt_response.currency,
                'dt_response': dt_response,
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
        account_id: str
    ) -> SummaryData:
        """Extract summary data from a single account's DataTablesResponse.

        This method extracts and caches summary data from a DataTablesResponse for
        a single account. Results are cached by account_id to avoid repeated extraction.

        :param dt_response: DataTablesResponse for a single account
        :param account_id: Account identifier for caching
        :return: SummaryData with extracted summary, currency, and account_id

        Example::

            >>> dt_response = DataTablesResponse(...)
            >>> summary_data = service._extract_summary_from_account(dt_response, '12345')
            >>> assert summary_data.account_id == '12345'
            >>> assert summary_data.currency == 'EUR'
        """
        # Check cache first
        if account_id in self._summary_cache:
            return self._summary_cache[account_id]

        # Build summary dict from AggregatedRow data
        summary: Dict[str, Dict[str, float]] = {}
        for agg_row in dt_response.data:
            month_display = agg_row.month.display
            category = agg_row.category
            amount = agg_row.total.raw

            if month_display not in summary:
                summary[month_display] = {}

            summary[month_display][category] = amount

        # Create and cache SummaryData
        summary_data = SummaryData(
            summary=summary,
            currency=dt_response.currency,
            account_id=account_id
        )
        self._summary_cache[account_id] = summary_data

        return summary_data
