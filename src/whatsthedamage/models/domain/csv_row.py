from dataclasses import dataclass
from typing import Optional

@dataclass
class CsvRow:
    date: str
    type: str
    partner: str
    amount: float
    currency: str
    category_id: str
    account: str
    notice: str
    confidence: Optional[float] = None

    def __init__(self, row: dict[str, str], mapping: dict[str, str]) -> None:
        """
        Initialize the CsvRow object with header values as attributes.

        :param row: Key-value pairs representing the CSV header and corresponding values.
        :param mapping: Mapping of standardized attributes to CSV headers.
        """
        self.date = row.get(mapping.get('date', ''), '').strip()
        self.type = row.get(mapping.get('type', ''), '').strip()
        self.partner = row.get(mapping.get('partner', ''), '').strip()
        self.amount = float(row.get(mapping.get('amount', ''), 0))
        self.currency = row.get(mapping.get('currency', ''), '').strip()
        self.category_id = row.get(mapping.get('category_id', ''), '').strip()
        self.account = row.get(mapping.get('account', ''), '').strip()
        self.notice = row.get(mapping.get('notice', ''), '').strip()
        self.confidence = None
