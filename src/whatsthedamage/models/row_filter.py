from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.dt_models import DateField
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

    def get_month_field(self, date_value: str) -> DateField:
        """
        Extract month information from a date and create a DateField with proper timestamp.

        Creates a DateField with:
        - display: Localized month name (e.g., 'January', 'February')
        - timestamp: Epoch timestamp of the first day of that month

        :param date_value: Date string to extract month from.
        :return: DateField with month name and timestamp.
        :raises ValueError: If the date_value is invalid or cannot be parsed.
        """
        if not date_value:
            raise ValueError("Date value cannot be None")

        try:
            date_obj = datetime.strptime(date_value, self._date_format)
            # Create first day of the month for timestamp
            first_day = datetime(date_obj.year, date_obj.month, 1)
            # Format as YYYY-MM-DD for epoch conversion
            first_day_str = first_day.strftime(self._date_format)
            month_timestamp = DateConverter.convert_to_epoch(first_day_str, self._date_format)
            # Display as localized month name
            month_display = DateConverter.convert_month_number_to_name(date_obj.month)
            return DateField(display=month_display, timestamp=month_timestamp)
        except ValueError:
            raise ValueError(f"Invalid date format for '{date_value}'")

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
        months: Dict[str, List[CsvRow]] = {}
        for row in self._rows:
            month_name = self.get_month_number(getattr(row, 'date'))
            if month_name is not None:
                if month_name not in months:
                    months[month_name] = []
                months[month_name].append(row)

        return tuple({k: v} for k, v in months.items())

    def filter_by_month_v2(self) -> Tuple[Tuple[DateField, List[CsvRow]], ...]:
        """
        Filter rows based on the month parsed from a specified attribute (v2).

        Returns tuples of (DateField, List[CsvRow]) instead of Dict[str, List[CsvRow]].
        The DateField contains both display value and proper timestamp based on the 
        actual year/month from the data.

        :return: A tuple of (DateField, List[CsvRow]) tuples.
        """
        months: Dict[str, Tuple[DateField, List[CsvRow]]] = {}
        for row in self._rows:
            date_value = getattr(row, 'date')
            month_field = self.get_month_field(date_value)
            # Use display value as key to group rows from the same month
            month_key = month_field.display

            if month_key not in months:
                months[month_key] = (month_field, [])
            months[month_key][1].append(row)

        # Return tuple of (DateField, rows) tuples
        return tuple(months.values())
