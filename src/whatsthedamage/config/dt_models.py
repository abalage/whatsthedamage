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
    date: DateField
    amount: DisplayRawField
    merchant: str
    currency: str
    account: str

class AggregatedRow(BaseModel):
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
    row: str  # category
    column: str  # month
    highlight_type: str  # e.g., 'outlier', 'pareto'

class StatisticalMetadata(BaseModel):
    highlights: List[CellHighlight]

@dataclass
class CachedProcessingResult:
    """Cached processing result dataclass."""
    responses: Dict[str, DataTablesResponse]
    metadata: StatisticalMetadata
