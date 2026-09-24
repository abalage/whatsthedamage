"""Correction service.

Service for managing user corrections and applying them to transactions.
"""

from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from whatsthedamage.models.repositories.correction_repository import CorrectionRepository
    from whatsthedamage.models.repositories.transaction_repository import TransactionRepository
    from whatsthedamage.models.database.correction import Correction
    from whatsthedamage.models.domain.csv_row import CsvRow


class CorrectionService:
    """Service for managing user corrections and applying them to transactions.

    Provides functionality for saving, retrieving, and applying user-specific
    corrections to transaction data. Corrections are matched case-insensitively
    based on the original_partner field.

    Attributes:
        correction_repo: Repository for correction database operations.
        transaction_repo: Repository for transaction database operations.
    """

    def __init__(
        self,
        correction_repo: 'CorrectionRepository',
        transaction_repo: 'TransactionRepository'
    ) -> None:
        """Initialize the correction service.

        Args:
            correction_repo: Repository for correction database operations.
            transaction_repo: Repository for transaction database operations.
        """
        self.correction_repo = correction_repo
        self.transaction_repo = transaction_repo

    def save_correction(
        self,
        user_id: int,
        original_partner: str,
        corrected_partner: Optional[str] = None,
        corrected_category_id: Optional[str] = None,
        corrected_notice: Optional[str] = None
    ) -> 'Correction':
        """Save a user correction for a merchant/partner name.

        Case-insensitive: stores original_partner in lowercase for lookup.
        If a correction for the same user and original_partner already exists,
        it is updated with the new values.

        Args:
            user_id: User identifier.
            original_partner: Original partner name to correct.
            corrected_partner: Corrected partner name (optional).
            corrected_category_id: Corrected category identifier (optional).
            corrected_notice: Corrected notice (optional).

        Returns:
            The saved Correction entity (either newly created or updated).
        """
        from whatsthedamage.models.database.correction import Correction

        existing = self.correction_repo.find_by_user_and_original_partner(
            user_id, original_partner
        )

        if existing:
            # Update existing correction using repository
            self.correction_repo.update(
                int(existing.id),
                corrected_partner=corrected_partner,
                corrected_category_id=corrected_category_id,
                corrected_notice=corrected_notice
            )
            # Return the existing correction (updated in database)
            return existing

        # Create new correction
        correction = Correction(
            user_id=user_id,
            original_partner=original_partner.lower(),
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id,
            corrected_notice=corrected_notice
        )
        return self.correction_repo.create(correction)

    def apply_corrections_to_row(
        self,
        user_id: int,
        csv_row: 'CsvRow'
    ) -> 'CsvRow':
        """Apply user's corrections to a CSV row based on original_partner lookup.

        Performs case-insensitive exact match lookup by original_partner.
        If a correction is found, returns a new CsvRow with the corrected values.
        Otherwise, returns the original CsvRow unchanged.

        Args:
            user_id: User identifier.
            csv_row: CSV row to apply corrections to.

        Returns:
            A CsvRow object with corrections applied (or original if no correction found).
        """
        from whatsthedamage.models.domain.csv_row import CsvRow

        correction = self.correction_repo.find_by_user_and_original_partner(
            user_id, csv_row.partner
        )

        if correction:
            # Create a copy of the csv_row by creating a new instance with the same values
            # We use object.__new__ to bypass the custom __init__ and then copy all attributes
            corrected_row = object.__new__(CsvRow)
            # Copy all attributes from the original row
            corrected_row.date = csv_row.date
            corrected_row.type = csv_row.type
            corrected_row.amount = csv_row.amount
            corrected_row.currency = csv_row.currency
            corrected_row.account = csv_row.account
            corrected_row.confidence = csv_row.confidence
            # Apply corrections to mutable fields
            corrected_row.partner = (
                str(correction.corrected_partner) if correction.corrected_partner else csv_row.partner
            )
            corrected_row.category_id = (
                str(correction.corrected_category_id) if correction.corrected_category_id else csv_row.category_id
            )
            corrected_row.notice = (
                str(correction.corrected_notice) if correction.corrected_notice else csv_row.notice
            )
            return corrected_row

        return csv_row

    def get_correction(
        self,
        user_id: int,
        original_partner: str
    ) -> Optional['Correction']:
        """Get correction for a specific original_partner.

        Args:
            user_id: User identifier.
            original_partner: Original partner name to look up.

        Returns:
            Correction entity if found, None otherwise.
        """
        return self.correction_repo.find_by_user_and_original_partner(
            user_id, original_partner
        )

    def delete_correction(
        self,
        user_id: int,
        original_partner: str
    ) -> bool:
        """Delete a correction for a user.

        Args:
            user_id: User identifier.
            original_partner: Original partner name of the correction to delete.

        Returns:
            True if correction was found and deleted, False otherwise.
        """
        correction = self.correction_repo.find_by_user_and_original_partner(
            user_id, original_partner
        )
        if correction:
            return self.correction_repo.delete(int(correction.id))
        return False

    def get_all_corrections(self, user_id: int) -> list['Correction']:
        """Get all corrections for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of all Correction entities for the user.
        """
        return self.correction_repo.find_by_user_id(user_id)

    def apply_corrections_to_rows(
        self,
        user_id: int,
        csv_rows: list['CsvRow']
    ) -> list['CsvRow']:
        """Apply corrections to a list of CSV rows.

        Args:
            user_id: User identifier.
            csv_rows: List of CSV rows to apply corrections to.

        Returns:
            List of CsvRow objects with corrections applied.
        """
        return [self.apply_corrections_to_row(user_id, row) for row in csv_rows]
