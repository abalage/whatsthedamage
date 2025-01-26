from typing import Any, Optional
from whatsthedamage.csv_row import CsvRow
from whatsthedamage.date_converter import DateConverter
from whatsthedamage.row_filter import RowFilter
from whatsthedamage.row_enrichment import RowEnrichment
from whatsthedamage.row_summarizer import RowSummarizer


class RowsProcessor:
    def __init__(self, config: Any):
        self.config = config

        self.date_attribute = config['csv']['date_attribute']
        self.date_attribute_format = config['csv']['date_attribute_format']
        self.sum_attribute = config['csv']['sum_attribute']
        self.selected_attributes = config['main']['selected_attributes']
        self.cfg_pattern_sets = config['enricher_pattern_sets']

        self._start_date = None
        self._end_date = None
        self._verbose = False
        self._category = None
        self._filter = None

    def set_start_date(self, start_date: Optional[str]):
        self._start_date = DateConverter.convert_to_epoch(
            start_date,
            self.date_attribute_format
        ) if start_date else None

    def set_end_date(self, end_date: Optional[str]):
        self._end_date = DateConverter.convert_to_epoch(
            end_date,
            self.date_attribute_format
        ) if end_date else None

    def set_verbose(self, verbose: bool):
        self._verbose = verbose

    def set_category(self, category: str):
        self._category = category

    def set_filter(self, filter: Optional[str]):
        self._filter = filter

    def print_categorized_rows(
            self,
            set_name: str,
            set_rows_dict: dict[str, list[CsvRow]],
            selected_attributes: list[str]) -> None:

        print(f"\nSet name: {set_name}")
        for type_value, rowset in set_rows_dict.items():
            print(f"\nType: {type_value}")
            for row in rowset:
                selected_values = {attr: getattr(row, attr, None) for attr in selected_attributes}
                print(selected_values)

    def process_rows(self, rows: list['CsvRow']) -> dict[str, dict[str, float]]:
        # Filter rows by date if start_date or end_date is provided
        row_filter = RowFilter(rows, self.date_attribute_format)
        if self._start_date and self._end_date:
            filtered_sets = row_filter.filter_by_date(self.date_attribute, self._start_date, self._end_date)
        else:
            filtered_sets = row_filter.filter_by_month(self.date_attribute)

        if self._verbose:
            print("Summary of attribute '" + self.sum_attribute + "' grouped by '" + self._category + "':")

        data_for_pandas = {}

        for filtered_set in filtered_sets:
            # set_name is the month or date range
            # set_rows is the list of CsvRow objects
            for set_name, set_rows in filtered_set.items():
                # Add attribute 'category' based on a specified other attribute matching against a set of patterns
                enricher = RowEnrichment(set_rows, self.cfg_pattern_sets)
                enricher.set_sum_attribute(self.sum_attribute)
                enricher.initialize()

                # Categorize rows by specificed attribute
                set_rows_dict = enricher.categorize_by_attribute(self._category)

                # Filter rows by category name if provided
                if self._filter:
                    set_rows_dict = {k: v for k, v in set_rows_dict.items() if k == self._filter}

                # Initialize the summarizer with the categorized rows
                summarizer = RowSummarizer(set_rows_dict, self.sum_attribute)

                # Summarize the values of the given attribute by category
                summary = summarizer.summarize()

                # Convert month number to name if set_name is a number
                try:
                    set_name = DateConverter.convert_month_number_to_name(int(set_name))
                except ValueError:
                    start_date_str = DateConverter.convert_from_epoch(
                        self._start_date,
                        self.date_attribute_format
                    ) if self._start_date else None
                    end_date_str = DateConverter.convert_from_epoch(
                        self._end_date,
                        self.date_attribute_format
                    ) if self._end_date else None
                    set_name = str(start_date_str) + " - " + str(end_date_str)

                data_for_pandas[set_name] = summary

                # Print categorized rows if verbose
                if self._verbose:
                    self.print_categorized_rows(set_name, set_rows_dict, self.selected_attributes)

        return data_for_pandas