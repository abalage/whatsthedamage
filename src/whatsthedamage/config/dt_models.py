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
    # currency: str
    # Add other fields as needed

class AggregatedRow(BaseModel):
    category: str
    total: DisplayRawField
    month: DateField
    details: List[DetailRow]

class DataTablesResponse(BaseModel):
    data: List[AggregatedRow]