from typing import Optional, Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.date_converter import DateConverter
from whatsthedamage.models.row_filter import RowFilter
from whatsthedamage.models.row_enrichment import RowEnrichment
from whatsthedamage.models.row_summarizer import RowSummarizer

"""
RowsProcessor processes rows of CSV data. It filters, enriches, categorizes, and summarizes the rows.
"""


class RowsProcessor:
    def __init__(self) -> None:
        """
        Initializes the RowsProcessor.
        """
        self._date_attribute_format: str = ''
        self._cfg_pattern_sets: Dict[str, Dict[str, List[str]]] = {}
        self._start_date: Optional[int] = None
        self._end_date: Optional[int] = None
        self._verbose = False
        self._category: str = ''
        self._filter: Optional[str] = None

    def set_date_attribute_format(self, date_attribute_format: str) -> None:
        """
        Sets the date attribute format.

        Args:
            date_attribute_format (str): The format of the date attribute.
        """
        self._date_attribute_format = date_attribute_format

    def set_cfg_pattern_sets(self, cfg_pattern_sets: Dict[str, Dict[str, List[str]]]) -> None:
        """
        Sets the configuration pattern sets.

        Args:
            cfg_pattern_sets (Dict[str, Dict[str, List[str]]]): Dictionary of pattern sets for the enricher.
        """
        self._cfg_pattern_sets = cfg_pattern_sets

    def set_start_date(self, start_date: Optional[str]) -> None:
        """
        Sets the start date.

        Args:
            start_date (Optional[str]): The start date as a string.
        """
        if start_date:
            formatted_date = DateConverter.convert_date_format(start_date, self._date_attribute_format)
            self._start_date = DateConverter.convert_to_epoch(formatted_date, self._date_attribute_format)
        else:
            self._start_date = None

    def set_end_date(self, end_date: Optional[str]) -> None:
        """
        Sets the end date.

        Args:
            end_date (Optional[str]): The end date as a string.
        """
        if end_date:
            formatted_date = DateConverter.convert_date_format(end_date, self._date_attribute_format)
            self._end_date = DateConverter.convert_to_epoch(formatted_date, self._date_attribute_format)
        else:
            self._end_date = None

    def set_verbose(self, verbose: bool) -> None:
        """
        Sets the verbose mode.

        Args:
            verbose (bool): Flag for verbose mode.
        """
        self._verbose = verbose

    def set_category(self, category: str) -> None:
        """
        Sets the category attribute.

        Args:
            category (str): The category attribute.
        """
        self._category = category

    def set_filter(self, filter: Optional[str]) -> None:
        """
        Sets the filter attribute.

        Args:
            filter (Optional[str]): The filter attribute.
        """
        self._filter = filter

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
        data_for_pandas = {}

        for filtered_set in filtered_sets:
            for set_name, set_rows in filtered_set.items():
                set_rows_dict = self._enrich_and_categorize_rows(set_rows)
                set_rows_dict = self._apply_filter(set_rows_dict)
                summary = self._summarize_rows(set_rows_dict)
                set_name = self._format_set_name(set_name)
                data_for_pandas[set_name] = summary

                if self._verbose:
                    self._print_categorized_rows(set_name, set_rows_dict)

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
        if self._start_date and self._end_date:
            return list(row_filter.filter_by_date(self._start_date, self._end_date))
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
                self._start_date, self._date_attribute_format) if self._start_date else "Unknown Start Date"
            end_date_str = DateConverter.convert_from_epoch(
                self._end_date, self._date_attribute_format) if self._end_date else "Unknown End Date"
            return f"{start_date_str} - {end_date_str}"

    def _print_categorized_rows(self, set_name: str, rows_dict: Dict[str, List[CsvRow]]) -> None:
        """
        Prints categorized rows from a dictionary.

        Args:
            set_name (str): The name of the set to be printed.
            rows_dict (Dict[str, List[CsvRow]]): A dictionary of type values and lists of CsvRow objects.

        Returns:
            None
        """
        print(f"\nSet name: {set_name}")
        for type_value, rowset in rows_dict.items():
            print(f"\nType: {type_value}")
            for row in rowset:
                print(repr(row))
