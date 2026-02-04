from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional
from dataclasses import dataclass
from whatsthedamage.models.api_models import ProcessingMetadata

class DisplayRawField(BaseModel):
    display: str
    raw: Any

class DateField(BaseModel):
    display: str
    timestamp: int

class DetailRow(BaseModel):
    row_id: str
    date: DateField
    amount: DisplayRawField
    merchant: str
    currency: str
    account: str

class AggregatedRow(BaseModel):
    row_id: str
    category: str
    total: DisplayRawField
    date: DateField
    details: List[DetailRow]
    is_calculated: bool = False

class CellHighlight(BaseModel):
    row_id: str  # Unique identifier referencing AggregatedRow or DetailRow
    highlight_type: str  # e.g., 'outlier', 'pareto', 'excluded'

class StatisticalMetadata(BaseModel):
    highlights: List[CellHighlight]

class DataTablesResponse(BaseModel):
    data: List[AggregatedRow]
    account: str = ""
    currency: str = ""
    result_id: str = ""
    metadata: Optional[Any] = None

class DetailedResponse(BaseModel):
    """Response model for v2 API (includes transaction details).

    Returns transaction-level details grouped by category and month.
    """
    data: List[AggregatedRow] = Field(
        description="List of aggregated rows with transaction details"
    )
    metadata: ProcessingMetadata = Field(
        description="Processing metadata"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "category": "grocery",
                        "total": {"display": "-45,000.00 HUF", "raw": -45000.00},
                        "month": {"display": "January 2024", "timestamp": 1704067200},
                        "details": [
                            {
                                "date": {"display": "2024-01-15", "timestamp": 1705276800},
                                "amount": {"display": "-12,500.00", "raw": -12500.00},
                                "merchant": "TESCO",
                                "currency": "HUF"
                            }
                        ]
                    }
                ],
                "metadata": {
                    "result_id": "550e8400-e29b-41d4-a716-446655440000",
                    "row_count": 1,
                    "processing_time": 0.23,
                    "ml_enabled": False
                }
            }
        }

@dataclass(frozen=True)
class SummaryData:
    """Extracted summary data from a DataTablesResponse for a single account.

    This model encapsulates the summary data extracted from transaction data,
    providing a simplified format for formatting and display.

    :param summary: Dict mapping column headers to category amounts.
                    Column headers are typically time periods (e.g., 'January', 'January (1704067200)').
                    Format: {column_header: {category: amount}}
    :type summary: Dict[str, Dict[str, float]]
    :param currency: Currency code (e.g., 'EUR', 'USD')
    :type currency: str
    :param account_id: Account identifier this summary belongs to
    :type account_id: str
    """
    summary: Dict[str, Dict[str, float]]
    currency: str
    account_id: str

@dataclass
class CachedProcessingResult:
    """Cached processing result dataclass."""
    responses: Dict[str, DataTablesResponse]
    metadata: StatisticalMetadata

@dataclass
class ProcessingResponse:
    """Complete response from CSV processing including data and metadata.

    This dataclass encapsulates the complete response from processing a CSV file,
    including the processed transaction data, processing metadata, and statistical
    analysis results.

    Attributes:
        result_id: Unique identifier for this processing result
        data: Dictionary mapping account IDs to their DataTablesResponse objects
        metadata: Processing metadata containing statistics (processing_time, row_count, etc.)
        statistical_metadata: Statistical analysis results including highlights
    """
    result_id: str
    data: Dict[str, DataTablesResponse]
    metadata: Any  # ProcessingMetadata
    statistical_metadata: StatisticalMetadata

