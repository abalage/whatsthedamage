from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from whatsthedamage.models.common.display_fields import DisplayRawField, DateField
from whatsthedamage.models.common.processing_metadata import ProcessingMetadata

if TYPE_CHECKING:
    from whatsthedamage.models.domain.account import Account


class PeriodData(TypedDict):
    """Type for period map values containing display name and category amounts."""
    display: str
    categories: dict[str, float]


class TransactionDetail(BaseModel):
    """Unified transaction detail model.

    Consolidates DetailRow (domain) and TransactionDetail (API) into a single
    model with all fields. Used for individual transactions within aggregated
    rows.

    Attributes:
        row_id (str): Unique row identifier.
        date (DateField): Transaction date.
        amount (DisplayRawField): Transaction amount.
        merchant (str): Merchant or transaction description.
        currency (str): Currency code.
        account (str): Account identifier.
        type (str | None): Transaction type.
        confidence (float | None): ML confidence score.
        notice (str | None): Transaction notice or memo.
        category_id (str | None): Category ID for drilldown.
        month_id (str | None): Month ID for drilldown.
    """
    row_id: str = Field(description="Unique row identifier")
    date: DateField = Field(description="Transaction date")
    amount: DisplayRawField = Field(description="Transaction amount")
    merchant: str = Field(description="Merchant or transaction description")
    currency: str = Field(default="", description="Currency code")
    account: str = Field(default="", description="Account identifier")
    type: str | None = Field(default=None, description="Transaction type")
    confidence: float | None = Field(
        default=None, description="ML confidence score"
    )
    notice: str | None = Field(
        default=None, description="Transaction notice or memo"
    )
    category_id: str | None = Field(
        default=None, description="Category ID for drilldown"
    )
    month_id: str | None = Field(
        default=None, description="Month ID for drilldown"
    )


# Backward compatibility alias - DetailRow is now TransactionDetail
DetailRow = TransactionDetail


class AggregatedRow(BaseModel):
    """Transactions grouped by category and date period.

    Represents aggregated transaction data for a specific category within a
    time period (typically a month). Contains the total amount and individual
    transaction details.

    Attributes:
        row_id (str): Unique row identifier.
        category_id (str): Category identifier.
        total (DisplayRawField): Total amount for this category/period.
        date (DateField): Date period (month).
        details (list[TransactionDetail]): Individual transactions in this group.
        is_calculated (bool): Whether this row was calculated (e.g., Balance,
            Total).
    """
    row_id: str = Field(description="Unique row identifier")
    category_id: str = Field(description="Category identifier")
    total: DisplayRawField = Field(
        description="Total amount for this category/period"
    )
    date: DateField = Field(description="Date period (month)")
    details: list[TransactionDetail] = Field(
        default_factory=list,
        description="Individual transactions in this group"
    )
    is_calculated: bool = Field(
        default=False,
        description="Whether this row was calculated (e.g., Balance, Total)"
    )

class CellHighlight(BaseModel):
    """Represents highlight metadata for a table cell.

    Attributes:
        row_id (str): Unique identifier referencing AggregatedRow or DetailRow.
        highlight_types (list[str]): List of highlight types for this row
            (e.g., ['outlier', 'pareto']).
    """
    row_id: str
    highlight_types: list[str]


class StatisticalMetadata(BaseModel):
    """Statistical analysis metadata for response data.

    Attributes:
        highlights (list[CellHighlight]): List of cell highlights from analysis.
    """
    highlights: list[CellHighlight]

class DetailedResponse(BaseModel):
    """Response model for v2 API (includes transaction details).

    Returns transaction-level details grouped by category and month.

    Attributes:
        data (list[AggregatedRow]): List of aggregated rows with transaction
            details.
        metadata (ProcessingMetadata): Processing metadata.
    """
    data: list[AggregatedRow] = Field(
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
                        "category_id": "grocery",
                        "total": {"display": "-45,000.00 HUF", "raw": -45000.00},
                        "date": {"display": "January 2024", "timestamp": 1704067200},
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
    """Extracted summary data from an AccountResponse for a single account.

    This model encapsulates the summary data extracted from transaction data,
    providing a simplified format for formatting and display.

    Attributes:
        summary (dict[str, dict[str, float]]): Dict mapping column headers to
            category amounts. Column headers are typically time periods
            (e.g., 'January', 'January (1704067200)').
            Format: {column_header: {category: amount}}
        currency (str): Currency code (e.g., 'EUR', 'USD').
        account_id (str): Account identifier this summary belongs to.
    """
    summary: dict[str, dict[str, float]]
    currency: str
    account_id: str

    @classmethod
    def from_datatable_response(
        cls,
        dt_response: "Account",
        account_id: str | None = None,
        include_calculated: bool = True
    ) -> 'SummaryData':
        """Create a SummaryData instance from an Account or AccountResponse.

        This is the canonical way to extract summary data from transaction data.
        Aggregates transaction data by month and category, creating a nested
        dictionary suitable for formatting and analysis.

        Parameters:
            dt_response (Account): Account containing aggregated transaction data.
            account_id (str | None): Optional account identifier (defaults to
                dt_response.id).
            include_calculated (bool): Whether to include calculated rows
                (e.g., Balance, Total).

        Returns:
            SummaryData: SummaryData instance with extracted summary.

        Example:
            >>> summary = SummaryData.from_datatable_response(dt_response)
            >>> summary.summary['January 2024']['Grocery']  # 1234.56
        """
        period_map = cls._aggregate_by_period(dt_response, include_calculated)
        display_counts = cls._count_display_occurrences(period_map)
        summary = cls._build_summary_dict(period_map, display_counts)
        response_account_id = getattr(dt_response, 'id', None)
        return cls(
            summary=summary,
            currency=dt_response.currency,
            account_id=account_id or response_account_id or ""
        )

    @classmethod
    def _aggregate_by_period(
        cls,
        dt_response: "Account",
        include_calculated: bool
    ) -> dict[int, PeriodData]:
        """Aggregate transaction data by timestamp period.

        Parameters:
            dt_response (Account): Account containing aggregated transaction data.
            include_calculated (bool): Whether to include calculated rows.

        Returns:
            dict[int, PeriodData]: Mapping of timestamps to period data
                containing display name and category amounts.
        """
        period_map: dict[int, PeriodData] = {}
        for agg_row in dt_response.data:
            if not include_calculated and getattr(agg_row, 'is_calculated', False):
                continue
            period_field = agg_row.date
            ts = period_field.timestamp
            display = period_field.display
            if ts not in period_map:
                period_map[ts] = {'display': display, 'categories': {}}
            cats = period_map[ts]['categories']
            cats[agg_row.category_id] = cats.get(agg_row.category_id, 0.0) + float(
                agg_row.total.raw
            )
        return period_map

    @classmethod
    def _count_display_occurrences(
        cls,
        period_map: dict[int, PeriodData]
    ) -> dict[str, int]:
        """Count occurrences of each display name in period map.

        Parameters:
            period_map (dict[int, PeriodData]): Period mapping from
                _aggregate_by_period.

        Returns:
            dict[str, int]: Count of each display name occurrence.
        """
        display_counts: dict[str, int] = {}
        for period_data in period_map.values():
            display = period_data['display']
            display_counts[display] = display_counts.get(display, 0) + 1
        return display_counts

    @classmethod
    def _build_summary_dict(
        cls,
        period_map: dict[int, PeriodData],
        display_counts: dict[str, int]
    ) -> dict[str, dict[str, float]]:
        """Build final summary dictionary with unique keys.

        Parameters:
            period_map (dict[int, PeriodData]): Period mapping from
                _aggregate_by_period.
            display_counts (dict[str, int]): Display name counts from
                _count_display_occurrences.

        Returns:
            dict[str, dict[str, float]]: Summary dictionary with unique keys,
                sorted by timestamp descending.
        """
        summary: dict[str, dict[str, float]] = {}
        for ts in sorted(period_map.keys(), reverse=True):
            period_data = period_map[ts]
            display = period_data['display']
            key = display if display_counts.get(display, 0) == 1 else f"{display} ({ts})"
            summary[key] = period_data['categories']
        return summary

@dataclass
class ProcessingResponse:
    """Complete response from CSV processing including data and metadata.

    This dataclass encapsulates the complete response from processing a CSV
    file, including the processed transaction data, processing metadata, and
    statistical analysis results.

    Attributes:
        result_id (str): Unique identifier for this processing result.
        data (dict[str, Account]): Dictionary mapping account IDs to their
            Account objects.
        metadata (ProcessingMetadata): Processing metadata containing statistics
            (processing_time, row_count, etc.).
        statistical_metadata (StatisticalMetadata): Statistical analysis results
            including highlights.
    """
    result_id: str
    data: dict[str, "Account"]
    metadata: ProcessingMetadata
    statistical_metadata: StatisticalMetadata


# Note: Circular dependency with Account model in account.py
# Both use string forward references and need model_rebuild() to be called after all imports

