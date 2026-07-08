"""Domain/business models for transaction processing.

This package provides a clean organization of domain-specific models.
"""

# CSV data models
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.models.domain.csv_file_handler import CsvFileHandler
from whatsthedamage.models.domain.csv_processor import CSVProcessor

# Aggregation models
from whatsthedamage.models.domain.dt_models import (
    AggregatedRow,
    DetailRow,
    DateField,
    DisplayRawField,
    ProcessingResponse,
    SummaryData,
    CellHighlight,
    StatisticalMetadata,
    DetailedResponse,
)
from whatsthedamage.models.domain.account import Account

# Resolve forward references for Account model
Account.model_rebuild()

# Builder
from whatsthedamage.models.domain.dt_response_builder import AccountResponseBuilder

# Calculators
from whatsthedamage.models.domain.dt_calculators import (
    create_balance_rows,
    create_total_spendings,
    create_cost_of_living_rows,
)

# Processing
from whatsthedamage.models.domain.row_filter import RowFilter
from whatsthedamage.models.domain.rows_processor import RowsProcessor
from whatsthedamage.models.domain.row_enrichment import RowEnrichment
from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML

# Statistics
from whatsthedamage.models.domain.statistical_algorithms import (
    StatisticalAlgorithm,
    IQROutlierDetection,
    ParetoAnalysis,
)

__all__ = [
    # CSV data models
    'CsvRow',
    'CsvFileHandler',
    'CSVProcessor',
    # Aggregation models
    'Account',
    'AggregatedRow',
    'DetailRow',
    'DateField',
    'DisplayRawField',
    'ProcessingResponse',
    'SummaryData',
    'CellHighlight',
    'StatisticalMetadata',
    'DetailedResponse',
    # Builder
    'AccountResponseBuilder',
    # Calculators
    'create_balance_rows',
    'create_total_spendings',
    'create_cost_of_living_rows',
    # Processing
    'RowFilter',
    'RowsProcessor',
    'RowEnrichment',
    'RowEnrichmentML',
    # Statistics
    'StatisticalAlgorithm',
    'IQROutlierDetection',
    'ParetoAnalysis',
]
