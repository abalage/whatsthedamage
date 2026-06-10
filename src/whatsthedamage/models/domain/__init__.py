"""Domain/business models for transaction processing.

This package contains all domain-specific models used for CSV processing,
data aggregation, and business logic.
"""

from whatsthedamage.models.domain.csv_data import CsvRow
from whatsthedamage.models.domain.aggregation import (
    AccountResponse,
    AggregatedRow,
    DetailRow,
    DateField,
    DisplayRawField,
)
from whatsthedamage.models.domain.value_objects import (
    CellHighlight,
    StatisticalMetadata,
)
from whatsthedamage.models.domain.processing import (
    ProcessingResponse,
    SummaryData,
    ProcessingResponse as ProcessingResponseDataclass,
)

# Re-export for backward compatibility during transition
from whatsthedamage.models.domain.aggregation import AccountResponse as DataTablesResponse
from whatsthedamage.models.domain.aggregation import AggregatedRow, DetailRow, DateField, DisplayRawField

__all__ = [
    # CSV data models
    'CsvRow',
    # Aggregation models
    'AccountResponse',
    'AggregatedRow',
    'DetailRow',
    'DateField',
    'DisplayRawField',
    # Value objects
    'CellHighlight',
    'StatisticalMetadata',
    # Processing models
    'ProcessingResponse',
    'SummaryData',
    # Backward compatibility aliases
    'DataTablesResponse',
]
