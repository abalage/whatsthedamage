from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
import json
import sys


# FIXME, this file belongs to the views module, but it is not used there yet.
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
    for type_value in sorted(rows_dict.keys()):
        print(f"\nType: {type_value}", file=sys.stderr)
        for row in sorted(rows_dict[type_value], key=lambda r: repr(r)):
            print(repr(row), file=sys.stderr)


def print_training_data(rows_dict: Dict[str, List[CsvRow]]) -> None:
    """
    Prints all objects of all rowsets from rows_dict as a JSON array to STDERR.

    Args:
        rows_dict (Dict[str, List[CsvRow]]): A dictionary of type values and lists of CsvRow objects.

    Returns:
        None
    """
    all_rows = []
    for rowset in rows_dict.values():
        for row in rowset:
            row_dict = row.__dict__.copy()
            all_rows.append(row_dict)
    print(json.dumps(all_rows, separators=(",", ":"), ensure_ascii=False), file=sys.stderr)
