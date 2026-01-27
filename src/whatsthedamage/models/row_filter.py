from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.dt_models import DateField
from whatsthedamage.config.config import AppContext
from typing import List, Dict, Tuple

import datetime


class RowFilter:
    def __init__(self, rows: List[CsvRow], context: AppContext) -> None:
        """
        Initialize the RowFilter with a list of CsvRow objects and a date format.

        :param rows: List of CsvRow objects to filter.
        :param date_format: The date format to use for filtering.
        """
        self._rows = rows
        self._date_format = context.config.csv.date_attribute_format

    def _get_month_field_id(self, date_value: str) -> DateField:
        # FIXME remove added datetime dependency, rework 'display' string creation
        """
        Extract month ID from a date and create a DateField with proper timestamp.

        Creates a DateField with:
        - display: Localized year and month name (e.g., '2023 January', '2023 január')
        - timestamp: Epoch timestamp of the first day of that month

        :param date_value: Date string to extract month from.
        :return: DateField with month name and timestamp.
        :raises ValueError: If the date_value is invalid or cannot be parsed.
        """
        # Use DateConverter primitives to keep business display logic here.
        timestamp = DateConverter.start_of_month_epoch(date_value, self._date_format)

        # Build a business-display string: Localized "YYYY <MonthName>"
        date_obj = datetime.datetime.fromtimestamp(timestamp)
        month = date_obj.month
        year = date_obj.year
        month_name = DateConverter.convert_month_number_to_name(month)
        display = f"{year} {month_name}"

        return DateField(display=display, timestamp=timestamp)

    def filter_by_date(
        self,
        start_date: float,
        end_date: float,
    ) -> List[Tuple[DateField, List[CsvRow]]]:
        """
        Filter rows based on a date range for a specified attribute.

        :param start_date: The start date in epoch time.
        :param end_date: The end date in epoch time.
        :return: A list with a single tuple containing the DateField for the range
                 and the list of matching CsvRow objects.
        """
        filtered_rows: list[CsvRow] = []
        for row in self._rows:
            date_value: int = DateConverter.convert_to_epoch(
                getattr(row, 'date'),
                self._date_format
            )

            if start_date <= date_value <= end_date:
                filtered_rows.append(row)

        # Build a DateField for the date range. Use the provided start_date epoch
        # as the canonical timestamp and a human-readable display for the range.
        start_date_str = DateConverter.convert_from_epoch(start_date, self._date_format)
        end_date_str = DateConverter.convert_from_epoch(end_date, self._date_format)
        range_field = DateField(display=f"{start_date_str} - {end_date_str}", timestamp=int(start_date))

        return [(range_field, filtered_rows)]


    def filter_by_month(self) -> List[Tuple[DateField, List[CsvRow]]]:
        """
        Filter rows based on the month parsed from a specified attribute.

        Returns tuples of (DateField, List[CsvRow]) instead of Dict[str, List[CsvRow]].
        The DateField contains both display value and proper timestamp based on the
        actual year/month from the data.

        :return: A tuple of (DateField, List[CsvRow]) tuples.
        """
        months: Dict[int, Tuple[DateField, List[CsvRow]]] = {}
        for row in self._rows:
            date_value = getattr(row, 'date')
            month_field_id = self._get_month_field_id(date_value)
            # Use timestamp as canonical grouping key (keeps year information)
            month_key_timestamp = month_field_id.timestamp

            if month_key_timestamp not in months:
                months[month_key_timestamp] = (month_field_id, [])
            months[month_key_timestamp][1].append(row)
        # Return list of (DateField, rows) tuples
        return list(months.values())

    def filter_by_account(self) -> Dict[str, List[CsvRow]]:
        """
        Filter rows by account, grouping transactions by account ID.

        Extracts the account attribute from each CsvRow and groups rows by account.
        Rows with missing or empty account values are grouped under "Unknown" key.

        :return: A dictionary mapping account ID to list of CsvRow objects.
        """
        accounts: Dict[str, List[CsvRow]] = {}
        for row in self._rows:
            account = getattr(row, 'account', '').strip()
            # Use "Unknown" for missing or empty account
            account_key = account if account else "Unknown"

            if account_key not in accounts:
                accounts[account_key] = []
            accounts[account_key].append(row)

        return accounts
