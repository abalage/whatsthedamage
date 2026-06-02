"""
Default calculator functions for DataTablesResponseBuilder.

Calculators are functions that receive a DataTablesResponseBuilder instance
and return a list of AggregatedRow objects. They are invoked sequentially
after all category data has been added to the builder.
"""

from typing import List, Dict, TYPE_CHECKING
from gettext import gettext as _
from whatsthedamage.models.dt_models import AggregatedRow

if TYPE_CHECKING:
    from whatsthedamage.models.dt_response_builder import DataTablesResponseBuilder


def create_balance_rows(builder: "DataTablesResponseBuilder") -> List[AggregatedRow]:
    """
    Default calculator that creates Balance category rows for each month.

    Balance represents the sum of all category totals for a given month.
    This function serves as a reference implementation of the calculator pattern.

    Args:
        builder: The DataTablesResponseBuilder instance with access to internal state.

    Returns:
        List[AggregatedRow]: List of Balance aggregated rows, one per month.
    """
    balance_rows = []
    for month_timestamp in sorted(builder._month_totals.keys()):
        month_field, total_amount = builder._month_totals[month_timestamp]

        # Use builder's public helper to create properly formatted row
        balance_row = builder.build_aggregated_row(
            category=_("Balance"),
            total_amount=total_amount,
            details=[],  # Balance has no detail rows
            date_field=month_field,
            is_calculated=True  # Mark as calculated data
        )
        balance_rows.append(balance_row)

    return balance_rows


def create_total_spendings(builder: "DataTablesResponseBuilder") -> List[AggregatedRow]:
    """
    Calculator that creates "Total Spendings" rows for each month.
    
    Sums all negative amounts (expenses) for each month as positive values,
    excluding calculated rows like Balance.
    
    Note: Category totals are passed as negative values for expenses (money going out).
    This calculator converts them to positive values to show spending amount.
    
    Args:
        builder: The DataTablesResponseBuilder instance with access to internal state.
    
    Returns:
        List[AggregatedRow]: List of Total Spendings aggregated rows, one per month.
    """
    month_totals = {}
    
    # Access builder's aggregated rows
    for row in builder._aggregated_rows:
        # Skip calculated rows like Balance and Total Spendings
        if row.is_calculated:
            continue
            
        month_timestamp = row.date.timestamp
        if month_timestamp not in month_totals:
            month_totals[month_timestamp] = (row.date, 0.0)
        
        # Sum negative amounts (expenses) as positive values
        if row.total.raw < 0:
            month_field_existing, current_total = month_totals[month_timestamp]
            month_totals[month_timestamp] = (month_field_existing, current_total + abs(row.total.raw))
    
    # Create rows using builder's helper method
    spendings_rows = []
    for month_timestamp in sorted(month_totals.keys()):
        month_field, total = month_totals[month_timestamp]
        spendings_row = builder.build_aggregated_row(
            category=_("Total Spendings"),
            total_amount=total,
            details=[],
            date_field=month_field,
            is_calculated=True  # Mark as calculated data
        )
        spendings_rows.append(spendings_row)

    return spendings_rows


def create_cost_of_living_rows(builder: "DataTablesResponseBuilder") -> List[AggregatedRow]:
    """
    Calculator that creates "Cost of Living" rows for each month.

    Sums all transaction amounts from the configured list of categories that
    represent essential living expenses.

    The default categories are defined in config.py (COST_OF_LIVING_CATEGORY_IDS).
    Categories are matched by their display names (from AVAILABLE_CATEGORIES.default_name).
    Users can customize their own Cost of Living definition on the frontend.

    Args:
        builder: The DataTablesResponseBuilder instance with access to internal state.

    Returns:
        List[AggregatedRow]: List of Cost of Living aggregated rows, one per month.
    """
    from whatsthedamage.config.config import COST_OF_LIVING_CATEGORY_IDS, AVAILABLE_CATEGORIES

    # Convert category IDs to display names for comparison
    # row.category contains display names (e.g., "Grocery"), not IDs (e.g., "grocery")
    cost_of_living_display_names = {
        cat.default_name for cat in AVAILABLE_CATEGORIES
        if cat.id in COST_OF_LIVING_CATEGORY_IDS
    }

    # Track totals per month
    month_totals: Dict[int, tuple] = {}

    # Iterate through all aggregated rows
    for row in builder._aggregated_rows:
        # Skip calculated rows
        if row.is_calculated:
            continue

        # Only include categories that are part of Cost of Living
        # Compare against display names since row.category contains display names
        if row.category not in cost_of_living_display_names:
            continue

        month_timestamp = row.date.timestamp

        if month_timestamp not in month_totals:
            month_totals[month_timestamp] = (row.date, 0.0)

        # Add to the running total for this month
        existing_field, current_total = month_totals[month_timestamp]
        month_totals[month_timestamp] = (existing_field, current_total + row.total.raw)

    # Create Cost of Living rows for each month
    col_rows = []
    for month_timestamp in sorted(month_totals.keys()):
        month_field, total = month_totals[month_timestamp]
        col_row = builder.build_aggregated_row(
            category=_("Cost of Living"),
            total_amount=total,
            details=[],  # No detail rows for calculated category
            date_field=month_field,
            is_calculated=True
        )
        col_rows.append(col_row)

    return col_rows
