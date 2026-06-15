from typing import Dict, List
from whatsthedamage.models.domain.dt_models import AccountResponse, DetailRow
from whatsthedamage.config.config import get_category_display_name
import json
import sys


def print_categorized_rows(responses_by_account: Dict[str, AccountResponse]) -> None:
    """
    Prints categorized rows from AccountResponse structures.

    Loops over accounts and prints separate sections with account headers.
    Extracts transaction data from AggregatedRow.details.
    Translates category IDs to display names for output.

    Args:
        responses_by_account (Dict[str, AccountResponse]): Mapping of account_id → AccountResponse.

    Returns:
        None
    """
    for account_id, dt_response in responses_by_account.items():
        print(f"\n=== Account: {account_id} ===", file=sys.stderr)

        # Group details by category display name
        category_rows: Dict[str, List[DetailRow]] = {}
        for agg_row in dt_response.data:
            category_display = get_category_display_name(agg_row.category_id)
            if category_display not in category_rows:
                category_rows[category_display] = []
            category_rows[category_display].extend(agg_row.details)

        # Print categorized rows
        for category_id in sorted(category_rows.keys()):
            print(f"\nCategory: {get_category_display_name(category_id)}", file=sys.stderr)
            # Sort by timestamp to keep ordering unambiguous across years
            for detail_row in sorted(category_rows[category_id], key=lambda r: f"{getattr(r.date, 'timestamp', 0)}_{r.merchant}_{r.amount.raw}"):
                # Format similar to CsvRow repr output
                print(f"DetailRow(date={detail_row.date.display}, amount={detail_row.amount.raw}, "
                      f"merchant={detail_row.merchant}, currency={detail_row.currency}, notice={detail_row.notice})", file=sys.stderr)


def print_training_data(responses_by_account: Dict[str, AccountResponse]) -> None:
    """
    Prints training data from AccountResponse structures as JSON array to STDERR.

    Extracts transaction data from AggregatedRow.details and formats as JSON.
    Strips account field for ML model compatibility.

    Args:
        responses_by_account (Dict[str, AccountResponse]): Mapping of account_id → AccountResponse.

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

    for account_id, dt_response in responses_by_account.items():
        for agg_row in dt_response.data:
            # Get display name for training data (ML training expects display names)
            #category_display = get_category_display_name(agg_row.category_id)
            for detail_row in agg_row.details:
                # Build dict matching CsvRow format (strip account for ML compatibility)
                row_dict = {
                    "amount": detail_row.amount.raw,
                    "category_id": agg_row.category_id,  # Use category_id for training data to match model input
                    "currency": detail_row.currency,
                    "date": detail_row.date.display,
                    "partner": detail_row.merchant,
                    "type": detail_row.type,
                }
                all_rows.append(row_dict)

    print(json.dumps(all_rows, separators=(",", ":"), ensure_ascii=False), file=sys.stderr)
