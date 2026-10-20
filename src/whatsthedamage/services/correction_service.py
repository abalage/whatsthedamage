"""Correction service.

Implements the merchant-rule upsert used by transaction corrections:
partner and category corrections upsert the user's merchant rule and,
when the user opted in to sharing, contribute the resulting rule to
the anonymized shared corrections.
"""

from typing import Any, Optional, cast

from flask import current_app

from whatsthedamage.models.database.correction import (
    Correction as CorrectionDB
)
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.correction_repository import (
    SqlAlchemyCorrectionRepository
)
from whatsthedamage.models.repositories.shared_correction_repository import (
    SqlAlchemySharedCorrectionRepository
)

MAX_SHARED_CATEGORY_ID_LENGTH = 50
MAX_SHARED_PARTNER_LENGTH = 255


class CorrectionService:
    """Service for merchant-rule corrections and sharing opt-in.

    Attributes:
        correction_repository: Repository for merchant rules.
        shared_correction_repository: Repository for anonymized
            shared corrections.
    """

    def __init__(
        self,
        correction_repository: SqlAlchemyCorrectionRepository,
        shared_correction_repository: (
            SqlAlchemySharedCorrectionRepository
        )
    ) -> None:
        """Initialize CorrectionService.

        Args:
            correction_repository: Repository for merchant rules.
            shared_correction_repository: Repository for anonymized
                shared corrections.
        """
        self.correction_repository = correction_repository
        self.shared_correction_repository = shared_correction_repository

    def upsert_rule(
        self,
        user_id: int,
        original_partner: str,
        corrected_partner: Optional[str] = None,
        corrected_category_id: Optional[str] = None
    ) -> CorrectionDB:
        """Update or create the merchant rule for an original partner.

        Only the provided fields are written; omitted fields keep
        their existing values (rule update) or stay None (rule
        creation).

        Args:
            user_id: Owning user identifier.
            original_partner: Original partner name the rule matches.
            corrected_partner: Corrected partner name, if provided.
            corrected_category_id: Corrected category identifier,
                if provided.

        Returns:
            The created or updated Correction entity.
        """
        existing = self.correction_repository.find_by_user_and_original_partner(
            user_id, original_partner
        )
        if existing:
            update_data: dict[str, Any] = {}
            if corrected_partner is not None:
                update_data['corrected_partner'] = corrected_partner
            if corrected_category_id is not None:
                update_data['corrected_category_id'] = corrected_category_id
            if update_data:
                self.correction_repository.update(
                    cast(int, existing.id), **update_data
                )
            return existing

        correction = CorrectionDB(
            user_id=user_id,
            original_partner=original_partner,
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id
        )
        return self.correction_repository.create(correction)

    def share_if_opted_in(
        self,
        user: UserDB,
        original_partner: str,
        corrected_partner: Optional[str],
        corrected_category_id: str
    ) -> None:
        """Contribute a merchant rule to the anonymized shared corrections.

        Shares merchant names and categories only; notices are never
        shared. The opt-in flag is evaluated per call, so revoking the
        opt-in takes effect immediately for future corrections. A
        sharing failure must not fail the correction write itself.

        Args:
            user: Authenticated user.
            original_partner: Original partner name of the merchant
                rule.
            corrected_partner: Corrected partner name, if any.
            corrected_category_id: Corrected category identifier.
        """
        if not user.opt_in_sharing:
            return

        if (
            not isinstance(corrected_category_id, str)
            or not corrected_category_id
            or len(corrected_category_id) > MAX_SHARED_CATEGORY_ID_LENGTH
        ):
            current_app.logger.warning(
                'Skipped shared correction contribution: '
                'invalid category value'
            )
            return

        if corrected_partner is not None and (
            not isinstance(corrected_partner, str)
            or len(corrected_partner) > MAX_SHARED_PARTNER_LENGTH
        ):
            current_app.logger.warning(
                'Skipped shared correction contribution: '
                'invalid partner value'
            )
            return

        try:
            self.shared_correction_repository.create_or_update(
                original_partner=original_partner,
                corrected_category_id=corrected_category_id,
                corrected_partner=corrected_partner,
                user_id=cast(int, user.id)
            )
        except Exception:
            current_app.logger.exception(
                'Failed to contribute shared correction'
            )

    def share_rule_if_opted_in(
        self, user: UserDB, original_partner: str
    ) -> None:
        """Contribute the user's current merchant rule if opted in.

        Re-fetches the persisted rule so the shared values reflect the
        actual rule state after the upsert, including fields not part
        of the current edit and explicit clears to None.

        Args:
            user: Authenticated user.
            original_partner: Original partner name of the merchant
                rule.
        """
        if not user.opt_in_sharing:
            return

        rule = self.correction_repository.find_by_user_and_original_partner(
            cast(int, user.id), original_partner
        )
        if not rule or not rule.corrected_category_id:
            return

        self.share_if_opted_in(
            user,
            original_partner,
            cast(Optional[str], rule.corrected_partner),
            cast(str, rule.corrected_category_id)
        )
