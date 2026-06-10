"""
Example: Using the Calculator Pattern with AccountResponseBuilder

This example demonstrates how to use the calculator pattern with default
and custom calculators.
"""

from whatsthedamage.models.dt_response_builder import AccountResponseBuilder
from whatsthedamage.models.dt_calculators import create_balance_rows, create_total_spendings

# Example Usage:

# 1. Use default calculators (Balance + Total Spendings)
builder_default = AccountResponseBuilder(
    currency="USD",
    date_format="%Y-%m-%d"
)
# Automatically includes Balance and Total Spendings rows


# 2. Disable all calculators
builder_no_calculators = AccountResponseBuilder(
    currency="USD",
    date_format="%Y-%m-%d",
    calculators=[]  # No calculated rows
)


# 3. Use custom calculator alongside defaults
builder_custom = AccountResponseBuilder(
    currency="USD",
    date_format="%Y-%m-%d",
    calculators=[
        create_balance_rows,      # Include Balance
        create_total_spendings    # Include Total Spendings (already default)
    ]
)


# 4. Use only Balance (disable Total Spendings)
builder_only_balance = AccountResponseBuilder(
    currency="USD",
    date_format="%Y-%m-%d",
    calculators=[
        create_balance_rows  # Only Balance, no Total Spendings
    ]
)
