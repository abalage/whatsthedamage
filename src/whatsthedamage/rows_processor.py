from typing import Optional, Dict, List
from whatsthedamage.csv_row import CsvRow
from whatsthedamage.date_converter import DateConverter
from whatsthedamage.row_filter import RowFilter
from whatsthedamage.row_enrichment import RowEnrichment
from whatsthedamage.row_summarizer import RowSummarizer

"""
RowsProcessor processes rows of CSV data. It filters, enriches, categorizes, and summarizes the rows.
"""


class RowsProcessor:
    def __init__(self) -> None:
        """
        Initializes the RowsProcessor.

        Attributes:
            date_attribute_format (str): The format of the date attribute.
            cfg_pattern_sets (dict): Dictionary of pattern sets for the enricher.
            _start_date (None): Placeholder for the start date.
            _end_date (None): Placeholder for the end date.
            _verbose (bool): Flag for verbose mode.
            _category (None): Placeholder for the category.
            _filter (None): Placeholder for the filter.
        """

        self._date_attribute_format: str = ''
        self._cfg_pattern_sets: Dict[str, Dict[str, List[str]]] = {}

        self._start_date: Optional[int] = None
        self._end_date: Optional[int] = None
        self._verbose = False
        self._category: str = ''
        self._filter: Optional[str] = None

    def set_date_attribute_format(self, date_attribute_format: str) -> None:
        self._date_attribute_format = date_attribute_format

    def set_cfg_pattern_sets(self, cfg_pattern_sets: Dict[str, Dict[str, List[str]]]) -> None:
        self._cfg_pattern_sets = cfg_pattern_sets

    def set_start_date(self, start_date: Optional[str]) -> None:
        if start_date:
            start_date = DateConverter.convert_date_format(start_date, self._date_attribute_format)
            self._start_date = DateConverter.convert_to_epoch(start_date, self._date_attribute_format)
        else:
            self._start_date = None

    def set_end_date(self, end_date: Optional[str]) -> None:
        if end_date:
            end_date = DateConverter.convert_date_format(end_date, self._date_attribute_format)
            self._end_date = DateConverter.convert_to_epoch(end_date, self._date_attribute_format)
        else:
            self._end_date = None

    def set_verbose(self, verbose: bool) -> None:
        self._verbose = verbose

    def set_category(self, category: str) -> None:
        self._category = category

    def set_filter(self, filter: Optional[str]) -> None:
        self._filter = filter

    def print_categorized_rows(
            self,
            set_name: str,
            set_rows_dict: dict[str, list[CsvRow]]) -> None:
        """
        Prints categorized rows from a dictionary.

        Args:
            set_name (str): The name of the set to be printed.
            set_rows_dict (dict[str, list[CsvRow]]): A dictionary of type values and a lists of CsvRow objects.

        Returns:
            None
        """
        print(f"\nSet name: {set_name}")
        for type_value, rowset in set_rows_dict.items():
            print(f"\nType: {type_value}")
            for row in rowset:
                print(row)

    def process_rows(self, rows: list[CsvRow]) -> dict[str, dict[str, float]]:
        """
        Processes a list of CsvRow objects and returns a summary of specified attributes grouped by a category.
        Args:
            rows (list[CsvRow]): List of CsvRow objects to be processed.
        Returns:
            dict[str, dict[str, float]]: A dictionary where keys are date ranges or month names, and values are
                                         dictionaries summarizing the specified attribute by category.
        The function performs the following steps:
        1. Filters rows by date if start_date or end_date is provided, otherwise filters by month.
        2. Enriches rows by adding a 'category' attribute based on specified patterns.
        3. Categorizes rows by the specified attribute.
        4. Filters rows by category name if a filter is provided.
        5. Summarizes the values of the given attribute by category.
        6. Converts month numbers to names or formats date ranges.
        7. Prints categorized rows if verbose mode is enabled.
        """

        # Filter rows by date if start_date or end_date is provided
        row_filter = RowFilter(rows, self._date_attribute_format)
        if self._start_date and self._end_date:
            filtered_sets = row_filter.filter_by_date(self._start_date, self._end_date)
        else:
            filtered_sets = row_filter.filter_by_month()

        if self._verbose:
            print("Summary of attribute 'amount' grouped by '" + self._category + "':")

        data_for_pandas = {}

        for filtered_set in filtered_sets:
            # set_name is the month or date range
            # set_rows is the list of CsvRow objects
            for set_name, set_rows in filtered_set.items():
                # Add attribute 'category' based on a specified other attribute matching against a set of patterns
                enricher = RowEnrichment(set_rows, self._cfg_pattern_sets)
                enricher.initialize()

                # Categorize rows by specified attribute
                if self._category:
                    set_rows_dict = enricher.categorize_by_attribute(self._category)
                else:
                    raise ValueError("Category attribute is not set")

                # Filter rows by category name if provided
                if self._filter:
                    set_rows_dict = {k: v for k, v in set_rows_dict.items() if k == self._filter}

                # Initialize the summarizer with the categorized rows
                summarizer = RowSummarizer(set_rows_dict)

                # Summarize the values of the given attribute by category
                summary = summarizer.summarize()

                # Convert month number to name if set_name is a number
                try:
                    set_name = DateConverter.convert_month_number_to_name(int(set_name))
                except (ValueError, TypeError):
                    start_date_str = DateConverter.convert_from_epoch(
                        self._start_date,
                        self._date_attribute_format
                    ) if self._start_date else "Unknown Start Date"
                    end_date_str = DateConverter.convert_from_epoch(
                        self._end_date,
                        self._date_attribute_format
                    ) if self._end_date else "Unknown End Date"
                    set_name = str(start_date_str) + " - " + str(end_date_str)

                data_for_pandas[set_name] = summary

                # Print categorized rows if verbose
                if self._verbose:
                    self.print_categorized_rows(set_name, set_rows_dict)

        return data_for_pandas
