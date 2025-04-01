from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow


def print_categorized_rows(set_name: str, rows_dict: Dict[str, List[CsvRow]]) -> None:
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
