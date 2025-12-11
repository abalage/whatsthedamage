"""
Default calculator functions for DataTablesResponseBuilder.

Calculators are functions that receive a DataTablesResponseBuilder instance
and return a list of AggregatedRow objects. They are invoked sequentially
after all category data has been added to the builder.
"""

from typing import List, TYPE_CHECKING
from gettext import gettext as _
from whatsthedamage.config.dt_models import AggregatedRow

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
            month_field=month_field
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
        if row.category in [_("Balance"), _("Total Spendings")]:
            continue
            
        month_timestamp = row.month.timestamp
        if month_timestamp not in month_totals:
            month_totals[month_timestamp] = (row.month, 0.0)
        
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
            month_field=month_field
        )
        spendings_rows.append(spendings_row)
    
    return spendings_rows
