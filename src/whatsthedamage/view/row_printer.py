from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.dt_models import DataTablesResponse, DetailRow
import json
import sys


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

    Example::

        [
            {
                "amount": -1890.0,
                "category": "Other",
                "currency": "HUF",
                "date": "1999.09.09",
                "partner": "Foo",
                "type": "Vásárlás belföldi kereskedőnél"
            },
            {
                "amount": -2292.0,
                "category": "Other",
                "currency": "HUF",
                "date": "1999.09.09",
                "partner": "Bar",
                "type": "Vásárlás belföldi kereskedőnél"
            }
        ]

    Returns:
        None
    """
    all_rows = []
    for rowset in rows_dict.values():
        for row in rowset:
            row_dict = row.__dict__.copy()
            all_rows.append(row_dict)
    print(json.dumps(all_rows, separators=(",", ":"), ensure_ascii=False), file=sys.stderr)


def print_categorized_rows_v2(responses_by_account: Dict[str, DataTablesResponse]) -> None:
    """
    Prints categorized rows from DataTablesResponse structures (v2).

    Loops over accounts and prints separate sections with account headers.
    Extracts transaction data from AggregatedRow.details.

    Args:
        responses_by_account (Dict[str, DataTablesResponse]): Mapping of account_id → DataTablesResponse.

    Returns:
        None
    """
    for account_id, dt_response in responses_by_account.items():
        print(f"\n=== Account: {account_id} ===", file=sys.stderr)

        # Group details by category
        category_rows: Dict[str, List[DetailRow]] = {}
        for agg_row in dt_response.data:
            category = agg_row.category
            if category not in category_rows:
                category_rows[category] = []
            category_rows[category].extend(agg_row.details)

        # Print categorized rows
        for category in sorted(category_rows.keys()):
            print(f"\nType: {category}", file=sys.stderr)
            for detail_row in sorted(category_rows[category], key=lambda r: f"{r.date.display}_{r.merchant}_{r.amount.raw}"):
                # Format similar to CsvRow repr output
                print(f"DetailRow(date={detail_row.date.display}, amount={detail_row.amount.raw}, "
                      f"merchant={detail_row.merchant}, currency={detail_row.currency})", file=sys.stderr)


def print_training_data_v2(responses_by_account: Dict[str, DataTablesResponse]) -> None:
    """
    Prints training data from DataTablesResponse structures as JSON array to STDERR (v2).

    Extracts transaction data from AggregatedRow.details and formats as JSON.
    Strips account field for ML model compatibility.

    Args:
        responses_by_account (Dict[str, DataTablesResponse]): Mapping of account_id → DataTablesResponse.

    Returns:
        None
    """
    all_rows = []

    for account_id, dt_response in responses_by_account.items():
        for agg_row in dt_response.data:
            category = agg_row.category
            for detail_row in agg_row.details:
                # Build dict matching CsvRow format (strip account for ML compatibility)
                row_dict = {
                    "amount": detail_row.amount.raw,
                    "category": category,
                    "currency": detail_row.currency,
                    "date": detail_row.date.display,
                    "partner": detail_row.merchant,
                    # Note: 'type' field not available in DetailRow, omitted for now
                }
                all_rows.append(row_dict)

    print(json.dumps(all_rows, separators=(",", ":"), ensure_ascii=False), file=sys.stderr)
