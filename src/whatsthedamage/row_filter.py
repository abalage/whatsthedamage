from whatsthedamage.date_converter import DateConverter
from whatsthedamage.csv_row import CsvRow
from datetime import datetime
from typing import Optional


class RowFilter:
    def __init__(self, rows: list['CsvRow'], date_format: str):
        """
        Initialize the RowFilter with a list of CsvRow objects and a date format.

        :param rows: List of CsvRow objects to filter.
        :param date_format: The date format to use for filtering.
        """
        self.rows = rows
        self.date_format = date_format
        self.months: tuple[dict[str, list['CsvRow']], ...] = (
            {"01": []}, {"02": []}, {"03": []}, {"04": []},
            {"05": []}, {"06": []}, {"07": []}, {"08": []},
            {"09": []}, {"10": []}, {"11": []}, {"12": []}
        )

    def get_month_number(self, date_value: Optional[str]) -> Optional[str]:
        """
        Extract the full month number from the date attribute.

        :param date_value: Received as string argument.
        :return: The full month number.
        """
        if date_value is not None:
            date_obj = datetime.strptime(date_value, self.date_format)
            return date_obj.strftime('%m')
        return None

    def filter_by_date(
            self,
            date_attribute: str,
            start_date: int,
            end_date: int) -> tuple[dict[str, list['CsvRow']], ...]:
        """
        Filter rows based on a date range for a specified attribute.

        :param date_attribute: The name of the date attribute to filter by.
        :param start_date: The start date in epoch time.
        :param end_date: The end date in epoch time.
        :return: A tuple of list of filtered CsvRow objects.
        """
        filtered_rows: list['CsvRow'] = []
        for row in self.rows:
            date_value: Optional[int] = DateConverter.convert_to_epoch(
                getattr(row, date_attribute, None),
                self.date_format
            )
            if date_value is not None:
                if (start_date is None or date_value >= start_date) and (end_date is None or date_value <= end_date):
                    filtered_rows.append(row)

        # FIXME '99' is a special key for rows that do not fall within the specified date range
        return {"99": filtered_rows},

    def filter_by_month(self, date_attribute: str) -> tuple[dict[str, list['CsvRow']], ...]:
        """
        Filter rows based on the month parsed from a specified attribute.

        :param date_attribute: The name of the date attribute to filter by.
        :return: A tuple of list of filtered CsvRow objects.
        """
        for row in self.rows:
            month_name = self.get_month_number(getattr(row, date_attribute, None))
            if month_name is not None:
                for month in self.months:
                    if month_name in month:
                        month[month_name].append(row)
        return self.months
