from pydantic import BaseModel
from typing import List, Any, Dict, Optional
from dataclasses import dataclass

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

class DataTablesResponse(BaseModel):
    data: List[AggregatedRow]
    account: str = ""
    currency: str = ""
    statistical_metadata: Optional['StatisticalMetadata'] = None

class CellHighlight(BaseModel):
    row_id: str  # Unique identifier referencing AggregatedRow or DetailRow
    highlight_type: str  # e.g., 'outlier', 'pareto', 'excluded'

class StatisticalMetadata(BaseModel):
    highlights: List[CellHighlight]

@dataclass
class CachedProcessingResult:
    """Cached processing result dataclass."""
    responses: Dict[str, DataTablesResponse]
    metadata: StatisticalMetadata
