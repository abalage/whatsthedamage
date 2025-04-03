from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.models.csv_row import CsvRow
from datetime import datetime
from typing import List, Dict, Tuple


class RowFilter:
    def __init__(self, rows: List[CsvRow], date_format: str) -> None:
        """
        Initialize the RowFilter with a list of CsvRow objects and a date format.

        :param rows: List of CsvRow objects to filter.
        :param date_format: The date format to use for filtering.
        """
        self._rows = rows
        self._date_format = date_format
        self._months: Tuple[Dict[str, List[CsvRow]], ...] = (
            {"01": []}, {"02": []}, {"03": []}, {"04": []},
            {"05": []}, {"06": []}, {"07": []}, {"08": []},
            {"09": []}, {"10": []}, {"11": []}, {"12": []}
        )

    def get_month_number(self, date_value: str) -> str:
        """
        Extract the full month number from the date attribute.

        :param date_value: Received as string argument.
        :return: The full month number.
        :raises ValueError: If the date_value is invalid or cannot be parsed.
        """
        if date_value:
            try:
                date_obj = datetime.strptime(date_value, self._date_format)
                return date_obj.strftime('%m')
            except ValueError:
                raise ValueError(f"Invalid date format for '{date_value}'")
        raise ValueError("Date value cannot be None")

    def filter_by_date(
            self,
            start_date: float,
            end_date: float) -> tuple[dict[str, list['CsvRow']], ...]:
        """
        Filter rows based on a date range for a specified attribute.

        :param start_date: The start date in epoch time.
        :param end_date: The end date in epoch time.
        :return: A tuple of list of filtered CsvRow objects.
        """
        filtered_rows: list['CsvRow'] = []
        for row in self._rows:
            date_value: int = DateConverter.convert_to_epoch(
                getattr(row, 'date'),
                self._date_format
            )

            if start_date <= date_value <= end_date:
                filtered_rows.append(row)

        # FIXME '99' is a special key for rows that do not fall within the specified date range
        return {"99": filtered_rows},

    def filter_by_month(self) -> Tuple[Dict[str, List[CsvRow]], ...]:
        """
        Filter rows based on the month parsed from a specified attribute.

        :return: A tuple of dictionaries with month names as keys and lists of filtered CsvRow objects as values.
        """
        for row in self._rows:
            month_name = self.get_month_number(getattr(row, 'date'))
            if month_name is not None:
                for month in self._months:
                    if month_name in month:
                        month[month_name].append(row)
        return self._months
