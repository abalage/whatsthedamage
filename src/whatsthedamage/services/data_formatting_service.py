"""Data Formatting Service for standardized data output formatting.

This service centralizes all data formatting logic across web, API, and CLI,
consolidating logic from DataFrameFormatter, html_parser, and various formatting
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
from whatsthedamage.utils.html_parser import TableParser


class DataFormattingService:
    """Service for formatting data into various output formats.

    This service consolidates formatting logic that was previously scattered across:
    - DataFrameFormatter for DataFrame/HTML formatting
    - html_parser.TableParser for HTML parsing
    - routes_helpers for sorting metadata injection
    - csv_processor for CSV export

    Supports multiple output formats:
    - HTML tables (with optional sorting metadata)
    - CSV strings
    - JSON strings
    - Currency formatting
    """

    def __init__(self) -> None:
        """Initialize the data formatting service."""
        self._table_parser = TableParser()

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

    def parse_html_table(
        self,
        html: str
    ) -> Tuple[List[str], List[List[str]]]:
        """Parse HTML table into headers and rows.

        :param html: HTML string containing a table
        :return: Tuple of (headers, rows) where headers is a list of column header
            strings and rows is a list of rows, each row is a list of cell values

        Example::

            >>> html = "<table><thead><tr><th>Cat</th></tr></thead></table>"
            >>> headers, rows = service.parse_html_table(html)
            >>> assert headers == ["Cat"]
        """
        return self._table_parser.parse_table(html)

    def prepare_table_for_rendering(
        self,
        html: str
    ) -> Tuple[List[str], List[List[Dict[str, Union[str, float, None]]]]]:
        """Parse HTML table and add sorting metadata for rendering.

        This method parses an HTML table and enhances it with sorting metadata
        needed for DataTables or sortable web tables. Each cell becomes a dict
        with 'display' (what to show) and 'order' (what to sort by).

        :param html: HTML table string
        :return: Tuple of (headers, enhanced_rows) where headers is a list of
            column header strings and enhanced_rows is a list of rows, each row
            is a list of dicts with 'display', 'order', and optionally 'details' keys

        Example::

            >>> html = "<table><thead><tr><th>Cat</th><th>Jan</th></tr></thead>"
            >>> html += "<tbody><tr><th>Grocery</th><td>150.50 EUR</td></tr></tbody></table>"
            >>> headers, rows = service.prepare_table_for_rendering(html)
            >>> assert rows[0][1]['display'] == "150.50 EUR"
            >>> assert rows[0][1]['order'] == 150.50
        """
        headers, raw_rows = self.parse_html_table(html)

        enhanced_rows: List[List[Dict[str, Union[str, float, None]]]] = []
        for row_data in raw_rows:
            enhanced_row: List[Dict[str, Union[str, float, None]]] = []
            for idx, cell in enumerate(row_data):
                # First column (categories) has no sorting order
                if idx == 0:
                    enhanced_row.append({
                        'display': cell,
                        'order': None
                    })
                else:
                    # Extract numeric value for sorting from currency strings
                    order_value = self._extract_sort_value(cell)
                    enhanced_row.append({
                        'display': cell,
                        'order': order_value
                    })
            enhanced_rows.append(enhanced_row)

        return headers, enhanced_rows

    def _extract_sort_value(self, cell_value: str) -> Union[float, str]:
        """Extract numeric value for sorting from formatted cell value.

        :param cell_value: Cell value string (e.g., "150.50 EUR" or "150.50")
        :return: Float value for sorting, or original string if not numeric

        Example::

            >>> service._extract_sort_value("150.50 EUR")
            150.50
            >>> service._extract_sort_value("N/A")
            "N/A"
        """
        if not cell_value or cell_value.strip() == '':
            return 0.0

        # Try to extract numeric value from currency strings like "150.50 EUR"
        parts = cell_value.strip().split()
        if len(parts) >= 1:
            try:
                return float(parts[0].replace(',', ''))
            except ValueError:
                pass

        # Try direct conversion
        try:
            return float(cell_value.replace(',', ''))
        except ValueError:
            return cell_value

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
