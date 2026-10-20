"""Data export service.

Builds the GDPR data export (right of access and data portability,
Art. 15 and 20): a single JSON-ready payload with the user's account
data, processing results, transactions, and corrections. Password and
recovery code hashes are never included.
"""

from datetime import datetime, UTC
from typing import Any, Optional, cast

from whatsthedamage.models.database.transaction import (
    Transaction as TransactionDB
)
from whatsthedamage.models.database.correction import (
    Correction as CorrectionDB
)
from whatsthedamage.models.database.processing_result import (
    ProcessingResult as ProcessingResultDB
)
from whatsthedamage.models.repositories.correction_repository import (
    SqlAlchemyCorrectionRepository
)
from whatsthedamage.models.repositories.processing_result_repository import (
    SqlAlchemyProcessingResultRepository
)
from whatsthedamage.models.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository
)


class DataExportService:
    """Service for exporting a user's personal data.

    Attributes:
        transaction_repository: Repository for transaction data.
        correction_repository: Repository for correction data.
        processing_result_repository: Repository for processing
            result data.
    """

    def __init__(
        self,
        transaction_repository: SqlAlchemyTransactionRepository,
        correction_repository: SqlAlchemyCorrectionRepository,
        processing_result_repository: (
            SqlAlchemyProcessingResultRepository
        )
    ) -> None:
        """Initialize DataExportService.

        Args:
            transaction_repository: Repository for transaction data.
            correction_repository: Repository for correction data.
            processing_result_repository: Repository for processing
                result data.
        """
        self.transaction_repository = transaction_repository
        self.correction_repository = correction_repository
        self.processing_result_repository = processing_result_repository

    def build_export(
        self,
        user_id: int,
        account_payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Build the complete personal data export payload.

        Args:
            user_id: Identifier of the exporting user.
            account_payload: API representation of the user's account.

        Returns:
            Dictionary with generated_at, account, processing
            results, transactions, and corrections.
        """
        transactions = self.transaction_repository.find_all_by_user(
            user_id
        )
        corrections = self.correction_repository.find_all_by_user(user_id)

        processing_results: list[dict[str, Any]] = []
        offset = 0
        page_size = 100
        while True:
            page = self.processing_result_repository.find_by_user_id(
                user_id, limit=page_size, offset=offset
            )
            processing_results.extend(
                self._result_payload(result) for result in page
            )
            if len(page) < page_size:
                break
            offset += page_size

        return {
            'generated_at': datetime.now(UTC).isoformat(),
            'account': account_payload,
            'processing_results': processing_results,
            'transactions': [
                self._transaction_payload(t) for t in transactions
            ],
            'corrections': [
                self._correction_payload(c) for c in corrections
            ]
        }

    @staticmethod
    def _to_iso(value: Any) -> Optional[str]:
        """Serialize a datetime-or-string value as an ISO 8601 string.

        Args:
            value: DateTime, string, or None.

        Returns:
            ISO 8601 string, the original string, or None.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _result_payload(self, result: ProcessingResultDB) -> dict[str, Any]:
        """Build the export payload of a processing result.

        Args:
            result: Processing result entity.

        Returns:
            Dictionary of the result's metadata.
        """
        return {
            'result_id': result.result_id,
            'csv_profile_id': result.csv_profile_id,
            'row_count': result.row_count,
            'processing_time': result.processing_time,
            'ml_enabled': result.ml_enabled,
            'start_date': self._to_iso(result.start_date),
            'end_date': self._to_iso(result.end_date),
            'created_at': self._to_iso(result.created_at)
        }

    def _transaction_payload(
        self, transaction: TransactionDB
    ) -> dict[str, Any]:
        """Build the export payload of a transaction.

        Args:
            transaction: Transaction entity.

        Returns:
            Dictionary of the transaction's data.
        """
        return {
            'id': transaction.id,
            'result_id': transaction.result_id,
            'date': self._to_iso(transaction.date),
            'transaction_type': transaction.transaction_type,
            'original_partner': transaction.original_partner,
            'amount': transaction.amount,
            'currency': transaction.currency,
            'account': transaction.account,
            'category_id': transaction.category_id,
            'partner': transaction.partner,
            'notice': transaction.notice,
            'confidence': transaction.confidence,
            'original_category_id': transaction.original_category_id,
            'original_notice': transaction.original_notice,
            'created_at': self._to_iso(transaction.created_at),
            'updated_at': self._to_iso(transaction.updated_at)
        }

    def _correction_payload(
        self, correction: CorrectionDB
    ) -> dict[str, Any]:
        """Build the export payload of a merchant-rule correction.

        Args:
            correction: Correction entity.

        Returns:
            Dictionary of the correction's data.
        """
        return {
            'id': correction.id,
            'original_partner': correction.original_partner,
            'corrected_partner': correction.corrected_partner,
            'corrected_category_id': correction.corrected_category_id,
            'created_at': self._to_iso(correction.created_at),
            'updated_at': self._to_iso(correction.updated_at)
        }
