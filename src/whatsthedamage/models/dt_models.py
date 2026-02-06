from pydantic import BaseModel, Field, ConfigDict
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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
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
    )

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

    @classmethod
    def from_datatable_response(
        cls,
        dt_response: DataTablesResponse,
        account_id: Optional[str] = None,
        include_calculated: bool = True
    ) -> 'SummaryData':
        """Create a SummaryData instance from a DataTablesResponse.

        This is the canonical way to extract summary data from transaction data.
        Aggregates transaction data by month and category, creating a nested dictionary
        suitable for formatting and analysis.

        Args:
            dt_response: DataTablesResponse containing aggregated transaction data
            account_id: Optional account identifier (defaults to dt_response.account)
            include_calculated: Whether to include calculated rows (e.g., Balance, Total)

        Returns:
            SummaryData instance with extracted summary

        Example:
            >>> summary = SummaryData.from_datatable_response(dt_response)
            >>> summary.summary['January 2024']['Grocery']  # 1234.56
        """
        # Aggregate by canonical timestamp first to keep year information unambiguous
        period_map: Dict[int, Dict[str, Any]] = {}

        for agg_row in dt_response.data:
            # Skip calculated rows if requested
            if not include_calculated and getattr(agg_row, 'is_calculated', False):
                continue

            period_field = agg_row.date
            ts = period_field.timestamp
            display = period_field.display

            if ts not in period_map:
                period_map[ts] = {'display': display, 'categories': {}}

            cats = period_map[ts]['categories']
            cats[agg_row.category] = cats.get(agg_row.category, 0.0) + float(agg_row.total.raw)

        # Handle duplicate month displays (e.g., 'January' across different years)
        # by appending timestamp if needed
        display_counts: Dict[str, int] = {}
        for v in period_map.values():
            display_counts[v['display']] = display_counts.get(v['display'], 0) + 1

        summary = {}
        # Iterate months in descending timestamp order (most recent first)
        for ts in sorted(period_map.keys(), reverse=True):
            display = period_map[ts]['display']
            key = display if display_counts.get(display, 0) == 1 else f"{display} ({ts})"
            summary[key] = period_map[ts]['categories']

        return cls(
            summary=summary,
            currency=dt_response.currency,
            account_id=account_id or dt_response.account
        )

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

