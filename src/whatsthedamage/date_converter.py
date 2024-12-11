from datetime import datetime, timezone
from typing import Optional


class DateConverter:
    @staticmethod
    def convert_to_epoch(date_str: Optional[str], date_format: str) -> Optional[int]:
        """
        Convert a date string to epoch time.

        :param date_str: The date string to convert.
        :param date_format: The format of the date string (e.g., '%Y.%m.%d').
        :return: The epoch time as an integer, or None if conversion fails.
        """
        if date_str:
            try:
                # Parse the date string and convert to epoch
                date_obj = datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
                return int(date_obj.timestamp())  # Convert to epoch
            except ValueError:
                print(f"Error: Invalid date format for '{date_str}'")
        return None

    @staticmethod
    def convert_from_epoch(epoch: Optional[float], date_format: str) -> Optional[str]:
        """
        Convert an epoch time to a date string.

        :param epoch: The epoch time to convert.
        :param date_format: The format to convert the epoch time to (e.g., '%Y.%m.%d').
        :return: The formatted date string.
        """
        if epoch:
            try:
                # Convert epoch to datetime object
                date_obj = datetime.fromtimestamp(epoch, tz=timezone.utc)
                return date_obj.strftime(date_format)  # Format the datetime object
            except (ValueError, OverflowError, OSError):
                print(f"Error: Invalid epoch value '{epoch}'")
                return None
        return None

    @staticmethod
    def convert_month_number_to_name(month_number: int) -> str:
        """
        Convert a month number to its corresponding month name.

        :param month_number (int or str): The month number to convert.
         Must be an integer or a string that can be converted to an integer between 1 and 12.
        :return the name of the month corresponding to the given month number.
        :raises ValueError: If the month number is not between 1 and 12.
        """
        month_number = int(month_number)
        if 1 <= month_number <= 12:
            return datetime(1900, month_number, 1).strftime('%B')
        else:
            raise ValueError("Invalid month number. Please enter a number between 1 and 12.")
