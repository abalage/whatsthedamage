from datetime import datetime, timezone
from typing import Optional
from dateutil import parser


class DateConverter:
    @staticmethod
    def convert_to_epoch(date_str: Optional[str], date_format: str) -> Optional[int]:
        """
        Convert a date string to epoch time.

        :param date_str: The date string to convert.
        :param date_format: The format of the date string (e.g., '%Y.%m.%d').
        :return: The epoch time as an integer, or None if conversion fails.
        :raises ValueError: If the date format is invalid.
        """
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
                return int(date_obj.timestamp())
            except ValueError:
                raise ValueError(f"Invalid date format for '{date_str}'")
        return None

    @staticmethod
    def convert_from_epoch(epoch: Optional[float], date_format: str) -> Optional[str]:
        """
        Convert an epoch time to a date string.

        :param epoch: The epoch time to convert.
        :param date_format: The format to convert the epoch time to (e.g., '%Y.%m.%d').
        :return: The formatted date string, or None if conversion fails.
        :raises ValueError: If the epoch value is invalid.
        """
        if epoch:
            try:
                date_obj = datetime.fromtimestamp(epoch, tz=timezone.utc)
                return date_obj.strftime(date_format)
            except (ValueError, OverflowError, OSError):
                raise ValueError(f"Invalid epoch value '{epoch}'")
        return None

    @staticmethod
    def convert_month_number_to_name(month_number: int) -> str:
        """
        Convert a month number to its corresponding month name.

        :param month_number: The month number to convert. Must be an integer between 1 and 12.
        :return: The name of the month corresponding to the given month number.
        :raises ValueError: If the month number is not between 1 and 12.
        """
        month_number = int(month_number)
        if 1 <= month_number <= 12:
            return datetime(1900, month_number, 1).strftime('%B')
        else:
            raise ValueError("Invalid month number. Please enter a number between 1 and 12.")

    @staticmethod
    def convert_date_format(date_str: str, date_format: str) -> str:
        """
        Convert a date string to the specified format.

        :param date_str: The date string to convert.
        :param date_format: The format to convert the date string to (e.g., '%Y-%m-%d').
        :return: The formatted date string.
        :raises ValueError: If the date format is not recognized.
        """
        try:
            date_obj: datetime = parser.parse(date_str)
            return date_obj.strftime(date_format)
        except ValueError:
            raise ValueError(f"Date format for '{date_str}' not recognized.")
