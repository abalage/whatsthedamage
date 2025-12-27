from typing import Optional, Dict, List, Union, Tuple
from whatsthedamage.config.config import AppContext, EnricherPatternSets
from whatsthedamage.config.dt_models import DataTablesResponse, DateField
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.row_enrichment import RowEnrichment
from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
from whatsthedamage.models.row_filter import RowFilter
from whatsthedamage.models.row_summarizer import RowSummarizer
from whatsthedamage.models.dt_response_builder import DataTablesResponseBuilder
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.view.row_printer import print_categorized_rows, print_training_data, print_categorized_rows_v2, print_training_data_v2

"""
RowsProcessor processes rows of CSV data. It filters, enriches, categorizes, and summarizes the rows.
"""


class RowsProcessor:
    def __init__(self, context: AppContext) -> None:
        """
        Initializes the RowsProcessor with the application context.

        Args:
            context (AppContext): The application context containing configuration and arguments.
        """
        self.context = context
        self._date_attribute_format: str = context.config.csv.date_attribute_format
        self._cfg_pattern_sets: EnricherPatternSets = context.config.enricher_pattern_sets
        self._start_date: Optional[str] = context.args.get("start_date", None)
        self._start_date_epoch: float = 0
        self._end_date: Optional[str] = context.args.get("end_date", None)
        self._end_date_epoch: float = 0
        self._verbose: bool = context.args.get("verbose", False)
        self._category: str = context.args.get("category", "")
        self._filter: Optional[str] = context.args.get("filter", None)
        self._training_data: bool = context.args.get("training_data", False)
        self._ml: bool = context.args.get("ml", False)
        self._dt_json_data: DataTablesResponse = DataTablesResponse(data=[])

        # Convert start and end dates to epoch if provided
        if self._start_date:
            formatted_start_date = DateConverter.convert_date_format(
                self._start_date, self._date_attribute_format
            )
            self._start_date_epoch = DateConverter.convert_to_epoch(
                formatted_start_date, self._date_attribute_format
            )
        if self._end_date:
            formatted_end_date = DateConverter.convert_date_format(
                self._end_date, self._date_attribute_format
            )
            self._end_date_epoch = DateConverter.convert_to_epoch(
                formatted_end_date, self._date_attribute_format
            )

    def get_currency_from_rows(self, rows: List[CsvRow]) -> str:
        """
        Extracts currency from the first available row.

        Args:
            rows (List[CsvRow]): List of CsvRow objects.

        Returns:
            str: The currency code, or empty string if no rows or currency not found.
        """
        if rows:
            return getattr(rows[0], 'currency', '')
        return ''

    def process_rows(self, rows: List[CsvRow]) -> Dict[str, Dict[str, float]]:
        """
        Processes a list of CsvRow objects and returns a summary of specified attributes grouped by a category.

        .. deprecated:: 0.9.0
            Use :func:`process_rows_v2` instead. This method will be removed in v0.10.0.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be processed.

        Returns:
            Dict[str, Dict[str, float]]: A dictionary where keys are date ranges or month names, and values are
                                         dictionaries summarizing the specified attribute by category.
        """
        import warnings
        warnings.warn(
            "process_rows() is deprecated. Use process_rows_v2() instead. "
            "This method will be removed in v0.10.0.",
            DeprecationWarning,
            stacklevel=2
        )
        filtered_sets = self._filter_rows(rows)
        data_for_pandas = {}
        all_set_rows_dict: Dict[str, List[CsvRow]] = {}

        for filtered_set in filtered_sets:
            for set_name, set_rows in filtered_set.items():
                set_rows_dict = self._enrich_and_categorize_rows(set_rows)
                set_rows_dict = self._apply_filter(set_rows_dict)
                summary = self._summarize_rows(set_rows_dict)
                formatted_set_name = self._format_set_name(set_name)
                data_for_pandas[formatted_set_name] = summary

                # Merge all categorized rows for training data/categorized print
                for cat, row_list in set_rows_dict.items():
                    if cat not in all_set_rows_dict:
                        all_set_rows_dict[cat] = []
                    all_set_rows_dict[cat].extend(row_list)

        # Only print once at the end
        if self._verbose:
            print_categorized_rows("All", all_set_rows_dict)
        elif self._training_data:
            print_training_data(all_set_rows_dict)

        return data_for_pandas

    def process_rows_v2(self, rows: List[CsvRow]) -> Dict[str, DataTablesResponse]:
        """
        Processes a list of CsvRow objects and returns per-account DataTablesResponse structures.

        Groups rows by account first, then processes each account independently.
        Each account gets its own Balance and Total Spendings calculations.
        Uses a builder pattern for transparent, step-by-step construction of the response.
        Uses v2 filtering that provides DateField objects with accurate timestamps.

        Args:
            rows (List[CsvRow]): List of CsvRow objects (potentially from multiple accounts).

        Returns:
            Dict[str, DataTablesResponse]: Mapping of account_id → DataTablesResponse.
        """
        # Group rows by account first
        row_filter = RowFilter(rows, self._date_attribute_format)
        rows_by_account = row_filter.filter_by_account()

        responses_by_account: Dict[str, DataTablesResponse] = {}

        # Process each account independently
        for account_id, account_rows in rows_by_account.items():
            # Filter rows by date or month for this account
            filtered_sets = self._filter_rows_v2(account_rows)

            # Initialize the builder with date format only
            builder = DataTablesResponseBuilder(self._date_attribute_format)

            # Process each month/date range for this account
            for month_field, set_rows in filtered_sets:
                # Enrich and categorize rows
                categorized_rows = self._enrich_and_categorize_rows(set_rows)
                categorized_rows = self._apply_filter(categorized_rows)

                # Summarize amounts by category
                summary = self._summarize_rows(categorized_rows)

                # Add each category to the builder with DateField
                for category, category_rows in categorized_rows.items():
                    builder.add_category_data(
                        category=category,
                        rows=category_rows,
                        total_amount=summary[category],
                        month_field=month_field
                    )

            # Build and store the final response for this account
            account_response = builder.build()

            # Store account identifier and currency in the response
            account_response.account = account_id
            account_response.currency = account_rows[0].currency if account_rows else ""

            responses_by_account[account_id] = account_response

        # Store first account's response for backward compatibility with get_dt_json_data
        if responses_by_account:
            first_account = next(iter(responses_by_account.keys()))
            self._dt_json_data = responses_by_account[first_account]

        # Print verbose/training_data output if flags are set
        if self._verbose:
            print_categorized_rows_v2(responses_by_account)
        elif self._training_data:
            print_training_data_v2(responses_by_account)

        return responses_by_account

    def get_dt_json_data(self) -> Optional[DataTablesResponse]:
        """
        Getter for the DataTables JSON structure.

        Returns:
            Optional[DataTablesResponse]: The DataTables-compatible JSON structure.
        """
        return self._dt_json_data

    def _filter_rows(self, rows: List[CsvRow]) -> List[Dict[str, List[CsvRow]]]:
        """
        Filters rows by date or month.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be filtered.

        Returns:
            List[Dict[str, List[CsvRow]]]: A list of dictionaries with filtered rows.
        """
        row_filter = RowFilter(rows, self._date_attribute_format)
        if self._start_date_epoch > 0 and self._end_date_epoch > 0:
            return list(row_filter.filter_by_date(self._start_date_epoch, self._end_date_epoch))
        return list(row_filter.filter_by_month())

    def _filter_rows_v2(self, rows: List[CsvRow]) -> List[Tuple[DateField, List[CsvRow]]]:
        """
        Filters rows by date or month (v2).

        Returns DateField objects with proper timestamps instead of string keys.
        For date ranges, creates a DateField with the start date.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be filtered.

        Returns:
            List[Tuple[DateField, List[CsvRow]]]: A list of tuples with DateField and filtered rows.
        """
        row_filter = RowFilter(rows, self._date_attribute_format)
        if self._start_date_epoch > 0 and self._end_date_epoch > 0:
            # For date range filtering, create a DateField with the start date
            filtered = row_filter.filter_by_date(self._start_date_epoch, self._end_date_epoch)
            # Convert to v2 format with DateField
            start_date_str = DateConverter.convert_from_epoch(
                self._start_date_epoch, self._date_attribute_format
            )
            # Create DateField for the date range
            date_field = DateField(
                display=f"{start_date_str} - {DateConverter.convert_from_epoch(self._end_date_epoch, self._date_attribute_format)}",
                timestamp=int(self._start_date_epoch)
            )
            # Return list of tuples
            return [(date_field, list(filtered[0].values())[0])]
        return list(row_filter.filter_by_month_v2())

    def _enrich_and_categorize_rows(self, rows: List[CsvRow]) -> Dict[str, List[CsvRow]]:
        """
        Enriches and categorizes rows by the specified attribute.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be enriched and categorized.

        Returns:
            Dict[str, List[CsvRow]]: A dictionary of categorized rows.

        Raises:
            ValueError: If the category attribute is not set.
        """
        if not self._category:
            raise ValueError("Category attribute is not set")
        enricher: Union[RowEnrichmentML, RowEnrichment]
        if self._ml:
            enricher = RowEnrichmentML(rows)
        else:
            enricher = RowEnrichment(rows, self._cfg_pattern_sets)
        return enricher.categorize_by_attribute(self._category)

    def _apply_filter(self, rows_dict: Dict[str, List[CsvRow]]) -> Dict[str, List[CsvRow]]:
        """
        Applies the filter to the categorized rows.

        Args:
            rows_dict (Dict[str, List[CsvRow]]): A dictionary of categorized rows.

        Returns:
            Dict[str, List[CsvRow]]: A dictionary of filtered rows.
        """
        if self._filter:
            return {k: v for k, v in rows_dict.items() if k == self._filter}
        return rows_dict

    def _summarize_rows(self, rows_dict: Dict[str, List[CsvRow]]) -> Dict[str, float]:
        """
        Summarizes the values of the given attribute by category.

        Args:
            rows_dict (Dict[str, List[CsvRow]]): A dictionary of categorized rows.

        Returns:
            Dict[str, float]: A dictionary summarizing the specified attribute by category.
        """
        summarizer = RowSummarizer(rows_dict)
        return summarizer.summarize()

    def _format_set_name(self, set_name: str) -> str:
        """
        Formats the set name by converting month numbers to names or formatting date ranges.

        Args:
            set_name (str): The set name to format.

        Returns:
            str: The formatted set name.
        """
        try:
            return DateConverter.convert_month_number_to_name(int(set_name))
        except (ValueError, TypeError):
            start_date_str = DateConverter.convert_from_epoch(
                self._start_date_epoch, self._date_attribute_format)
            end_date_str = DateConverter.convert_from_epoch(
                self._end_date_epoch, self._date_attribute_format)
            return f"{start_date_str} - {end_date_str}"

    def _format_month_name(self, month_field: DateField) -> str:
        """
        Returns the month name from a DateField.

        The DateField.display already contains the localized month name or date range.

        Args:
            month_field (DateField): The DateField containing month information.

        Returns:
            str: The month name or date range.
        """
        return month_field.display
