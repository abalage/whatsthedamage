from pydantic import BaseModel
from typing import List, Any

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
    month: DateField
    date: DateField
    details: List[DetailRow]

class DataTablesResponse(BaseModel):
    data: List[AggregatedRow]
    account: str = ""
    currency: str = ""

class CellHighlight(BaseModel):
    row: str  # category
    column: str  # month
    highlight_type: str  # e.g., 'outlier', 'pareto'

class StatisticalMetadata(BaseModel):
    highlights: List[CellHighlight]

class CachedProcessingResult(BaseModel):
    responses: Dict[str, DataTablesResponse]
    metadata: StatisticalMetadata