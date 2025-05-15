from typing import Optional, Dict, List
from whatsthedamage.config.config import AppContext, EnricherPatternSets
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.row_enrichment import RowEnrichment
from whatsthedamage.models.row_filter import RowFilter
from whatsthedamage.models.row_summarizer import RowSummarizer
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.utils.row_printer import print_categorized_rows

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
        self._currency: str = ""

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

    def get_currency(self) -> str:
        """
        Getter for the currency.

        Returns:
            Optional[str]: The currency value.
        """
        return self._currency

    def set_currency(self, filtered_sets: List[Dict[str, List[CsvRow]]]) -> None:
        """
        Setter for the currency. Determines the currency based on filtered_sets.

        Args:
            filtered_sets (List[Dict[str, List[CsvRow]]]): Filtered sets of rows.
        """
        self._currency = next(
            (set_rows[0].currency for filtered_set in filtered_sets for set_rows in filtered_set.values() if set_rows),
            ""
        )

    def process_rows(self, rows: List[CsvRow]) -> Dict[str, Dict[str, float]]:
        """
        Processes a list of CsvRow objects and returns a summary of specified attributes grouped by a category.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be processed.

        Returns:
            Dict[str, Dict[str, float]]: A dictionary where keys are date ranges or month names, and values are
                                         dictionaries summarizing the specified attribute by category.
        """
        filtered_sets = self._filter_rows(rows)
        self.set_currency(filtered_sets)
        data_for_pandas = {}

        for filtered_set in filtered_sets:
            for set_name, set_rows in filtered_set.items():
                set_rows_dict = self._enrich_and_categorize_rows(set_rows)
                set_rows_dict = self._apply_filter(set_rows_dict)
                summary = self._summarize_rows(set_rows_dict)
                set_name = self._format_set_name(set_name)
                data_for_pandas[set_name] = summary

                if self._verbose:
                    print_categorized_rows(set_name, set_rows_dict)

        return data_for_pandas

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
        enricher = RowEnrichment(rows, self._cfg_pattern_sets)
        enricher.initialize()
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
