"""Transaction import service.

Implements CSV-import persistence: extracting CSV rows from a
processing response and persisting the processing result with its
transactions atomically through the unit of work, applying the user's
merchant rules and skipping deduplication duplicates.
"""

from datetime import datetime, UTC
from typing import Any, Optional

from whatsthedamage.models.api.requests import ProcessingRequest
from whatsthedamage.models.database.transaction import (
    Transaction as TransactionDB
)
from whatsthedamage.models.domain.dt_models import ProcessingResponse
from whatsthedamage.models.repositories.unit_of_work import (
    SqlAlchemyUnitOfWork
)
from whatsthedamage.services.deduplication_service import (
    DeduplicationService
)
from whatsthedamage.utils.date_converter import DateConverter


class TransactionImportService:
    """Service for persisting processing results and their transactions.

    Attributes:
        deduplication_service: Service computing deduplication hashes.
    """

    def __init__(
        self,
        deduplication_service: DeduplicationService
    ) -> None:
        """Initialize TransactionImportService.

        Args:
            deduplication_service: Service computing deduplication
                hashes.
        """
        self.deduplication_service = deduplication_service

    def extract_csv_rows_from_result(
        self, result: ProcessingResponse
    ) -> list[Any]:
        """Collect the individual CSV rows of a processing response.

        Args:
            result: Complete processing response with per-account data.

        Returns:
            List of CsvRow objects, one per transaction detail.
        """
        from whatsthedamage.models.domain.csv_row import CsvRow

        all_csv_rows: list[Any] = []
        for account in result.data.values():
            if hasattr(account, 'data') and account.data:
                for agg_row in account.data:
                    if hasattr(agg_row, 'details') and agg_row.details:
                        for detail in agg_row.details:
                            csv_row_dict: dict[str, str] = {
                                'date': datetime.fromtimestamp(
                                    detail.date.timestamp, tz=UTC
                                ).strftime('%Y-%m-%d'),
                                'type': detail.type or '',
                                'partner': detail.merchant or '',
                                'amount': str(detail.amount.raw),
                                'currency': detail.currency or '',
                                'category_id': detail.category_id or '',
                                'account': detail.account or '',
                                'notice': detail.notice or '',
                                'confidence': (
                                    str(detail.confidence)
                                    if detail.confidence is not None
                                    else ''
                                )
                            }
                            all_csv_rows.append(CsvRow(csv_row_dict,
                                {'date': 'date', 'type': 'type',
                                 'partner': 'partner',
                                 'amount': 'amount',
                                 'currency': 'currency',
                                 'category_id': 'category_id',
                                 'account': 'account',
                                 'notice': 'notice'}))
        return all_csv_rows

    def extract_result_date_range(
        self,
        metadata: Any,
        params: ProcessingRequest
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Resolve the processing result date range.

        Prefers dates reported in the processing metadata, falling
        back to the request parameters. Values are parsed into
        datetimes for persistence in the processing result's DateTime
        columns.

        Args:
            metadata: Processing metadata from the processing response.
            params: Validated request parameters.

        Returns:
            Tuple of (start_date, end_date), either may be None.
        """
        start_date_val = None
        end_date_val = None
        date_range = getattr(metadata, 'date_range', None)
        if date_range:
            start_date_val = getattr(date_range, 'start', None)
            end_date_val = getattr(date_range, 'end', None)
        if start_date_val is None:
            start_date_val = params.start_date or None
        if end_date_val is None:
            end_date_val = params.end_date or None
        return (
            self._parse_result_date(start_date_val),
            self._parse_result_date(end_date_val)
        )

    @staticmethod
    def _parse_result_date(value: Any) -> Optional[datetime]:
        """Parse a date filter string into a datetime for persistence.

        Args:
            value: Date value (string or datetime); may be None.

        Returns:
            Parsed datetime, or None when the value is missing or
            unparseable.
        """
        if isinstance(value, datetime) or not value:
            return value
        try:
            return DateConverter.parse_to_datetime_utc(value)
        except ValueError:
            pass
        try:
            from dateutil import parser as dateutil_parser
            return dateutil_parser.parse(str(value))
        except (ValueError, OverflowError):
            return None

    def persist_result_transactions(
        self,
        user_id: int,
        result_id: str,
        csv_rows: list[Any],
        uow: SqlAlchemyUnitOfWork
    ) -> None:
        """Persist transaction entities, skipping deduplication duplicates.

        Runs inside the given unit of work without committing; rows
        already present in the database and rows repeated within the
        batch are skipped. The user's merchant rules (partner and
        category only; notices are per-transaction) are looked up once
        by original partner (case-insensitive exact match) and applied
        to the newly stored transactions; the deduplication hash is
        always computed from the original row, so rules never alter
        the deduplication key. The raw processing values are preserved
        in the original_* columns.

        Args:
            user_id: User identifier owning the transactions.
            result_id: Processing result the transactions belong to.
            csv_rows: CSV rows to persist.
            uow: Unit of work providing the transaction repository and
                controlling commit/rollback.
        """
        dedup_hashes = [
            self.deduplication_service.generate_dedup_hash_from_row(
                csv_row
            )
            for csv_row in csv_rows
        ]
        existing_hashes = uow.transactions.find_existing_dedup_hashes(
            user_id, dedup_hashes
        )

        correction_map = {
            c.original_partner.lower(): c
            for c in uow.corrections.find_all_by_user(user_id)
        }

        new_transactions: list[TransactionDB] = []
        batch_hashes: set[str] = set()
        for csv_row, dedup_hash in zip(csv_rows, dedup_hashes):
            if dedup_hash in existing_hashes or dedup_hash in batch_hashes:
                continue
            batch_hashes.add(dedup_hash)
            correction = correction_map.get(csv_row.partner.lower())
            raw_category_id = getattr(csv_row, 'category_id', None)
            raw_notice = getattr(csv_row, 'notice', None)
            new_transactions.append(TransactionDB(
                user_id=user_id,
                result_id=result_id,
                date=DateConverter.parse_to_datetime_utc(csv_row.date),
                transaction_type=csv_row.type,
                original_partner=csv_row.partner,
                amount=float(csv_row.amount),
                currency=csv_row.currency,
                account=csv_row.account or 'unknown',
                deduplication_hash=dedup_hash,
                category_id=(
                    correction.corrected_category_id
                    if correction and correction.corrected_category_id
                    else raw_category_id
                ),
                partner=(
                    correction.corrected_partner
                    if correction and correction.corrected_partner
                    else None
                ),
                notice=raw_notice,
                original_category_id=raw_category_id,
                original_notice=raw_notice,
                confidence=getattr(csv_row, 'confidence', None),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            ))

        uow.transactions.add_all(new_transactions)
