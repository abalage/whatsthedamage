"""Data retention service.

Implements the retention policy (see docs/retention-policy.md):

- Users can request account deletion; the deletion is scheduled with
  a grace period during which logging in cancels it. The request may
  also ask for the user's shared correction contributions to be
  withdrawn (GDPR Art. 7(3), default off).
- The purge job deletes accounts whose grace period has elapsed and
  the accounts of users inactive for longer than the inactivity
  window, together with all of their personal data. Shared
  corrections are anonymized and retained unless the user requested
  their withdrawal with the account deletion.
- The purge job also deletes expired and revoked session rows
  (they contain IP address and user agent data).
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Optional, cast

from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.user_repository import (
    SqlAlchemyUserRepository
)
from whatsthedamage.models.repositories.session_repository import (
    SqlAlchemySessionRepository
)
from whatsthedamage.models.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository
)
from whatsthedamage.models.repositories.correction_repository import (
    SqlAlchemyCorrectionRepository
)
from whatsthedamage.models.repositories.processing_result_repository import (
    SqlAlchemyProcessingResultRepository
)
from whatsthedamage.models.repositories.shared_correction_repository import (
    SqlAlchemySharedCorrectionRepository
)
from whatsthedamage.services.password_service import PasswordService
from whatsthedamage.utils.logging import get_logger


class RetentionService:
    """Service for data retention and account deletion.

    Orchestrates account deletion requests and the periodic purge
    that permanently deletes accounts (and all of their personal
    data) of users past their deletion grace period or inactive for
    longer than the retention window. Uses dependency injection for
    all required services and repositories.

    Attributes:
        user_repository: Repository for user data access.
        session_repository: Repository for session data access.
        password_service: Service for password verification.
        transaction_repository: Repository for transaction data access.
        correction_repository: Repository for correction data access.
        processing_result_repository: Repository for processing
            result data access.
        shared_correction_repository: Repository for shared
            correction data access (contribution withdrawal).
        deletion_grace_days: Grace period (in days) between an
            account deletion request and the actual purge.
        inactivity_days: Days without a login after which the purge
            job deletes a user's personal data.
        logger: Logger instance for audit logging.
    """

    def __init__(
        self,
        user_repository: SqlAlchemyUserRepository,
        session_repository: SqlAlchemySessionRepository,
        password_service: PasswordService,
        transaction_repository: SqlAlchemyTransactionRepository,
        correction_repository: SqlAlchemyCorrectionRepository,
        processing_result_repository: SqlAlchemyProcessingResultRepository,
        shared_correction_repository: (
            SqlAlchemySharedCorrectionRepository
        ),
        deletion_grace_days: int = 7,
        inactivity_days: int = 180
    ):
        """Initialize RetentionService.

        Args:
            user_repository: Repository for user data access.
            session_repository: Repository for session data access.
            password_service: Service for password verification.
            transaction_repository: Repository for transaction data
                access.
            correction_repository: Repository for correction data
                access.
            processing_result_repository: Repository for processing
                result data access.
            shared_correction_repository: Repository for shared
                correction data access (contribution withdrawal).
            deletion_grace_days: Grace period (in days) between an
                account deletion request and the actual purge.
            inactivity_days: Days without a login after which the
                purge job deletes a user's personal data.
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.password_service = password_service
        self.transaction_repository = transaction_repository
        self.correction_repository = correction_repository
        self.processing_result_repository = processing_result_repository
        self.shared_correction_repository = shared_correction_repository
        self.deletion_grace_days = deletion_grace_days
        self.inactivity_days = inactivity_days
        self.logger = get_logger(__name__)

    def request_account_deletion(
        self,
        user: UserDB,
        password: str,
        revoke_shared_corrections: bool = False
    ) -> datetime:
        """Schedule the user's account deletion.

        Verifies the user's password, schedules the deletion after the
        grace period, records whether the user's shared correction
        contributions must be withdrawn with the account, and revokes
        all of the user's sessions. Logging in before the scheduled
        timestamp cancels the deletion (and the withdrawal request).

        Args:
            user: The authenticated user requesting deletion.
            password: Current password for confirmation.
            revoke_shared_corrections: Whether the user's shared
                correction contributions must be withdrawn when the
                account is deleted (default False).

        Returns:
            The UTC timestamp after which the account is deleted.

        Raises:
            ValueError: If the password is incorrect.
        """
        if not self.password_service.verify_password(
            password, cast(str, user.password_hash)
        ):
            self.logger.warning(
                "Account deletion request failed: invalid password",
                extra={"context": {
                    "action": "account_deletion",
                    "status": "failed",
                    "reason": "invalid_password",
                    "user_id": user.id
                }}
            )
            raise ValueError("Invalid password")

        scheduled_deletion_at = datetime.now(UTC) + timedelta(
            days=self.deletion_grace_days
        )

        self.user_repository.schedule_deletion(
            cast(int, user.id),
            scheduled_deletion_at,
            revoke_shared_corrections=revoke_shared_corrections
        )
        self.session_repository.revoke_by_user_id(cast(int, user.id))

        self.logger.info(
            "Account deletion scheduled",
            extra={"context": {
                "action": "account_deletion",
                "status": "scheduled",
                "user_id": user.id,
                "scheduled_deletion_at": scheduled_deletion_at.isoformat(),
                "revoke_shared_corrections": revoke_shared_corrections
            }}
        )
        return scheduled_deletion_at

    def purge(self, now: Optional[datetime] = None) -> dict[str, int]:
        """Run the retention purge job.

        Deletes accounts whose deletion grace period has elapsed and
        the accounts of users inactive for longer than the inactivity
        window, together with all of their personal data. Deletion is
        permanent; an inactive user must register a new account.
        Shared corrections of a deleted user are withdrawn when the
        user requested revocation with the account deletion; other
        shared corrections are anonymized and retained. Expired and
        revoked session rows (IP address, user agent) are physically
        deleted as deletion proof. Intended to be run periodically,
        e.g. daily via the ``flask retention-purge`` command.

        Args:
            now: Current UTC timestamp; defaults to the actual time.

        Returns:
            Mapping of purge result counts:
            ``accounts_deleted`` (grace period elapsed),
            ``inactive_accounts_deleted``, and
            ``expired_sessions_deleted``.
        """
        if now is None:
            now = datetime.now(UTC)

        accounts_deleted = self._purge_due_deletions(now)
        inactive_accounts_deleted = self._purge_inactive_users(now)
        expired_sessions_deleted = (
            self.session_repository.cleanup_expired_and_revoked()
        )
        if expired_sessions_deleted:
            self.logger.info(
                "Expired and revoked sessions deleted",
                extra={"context": {
                    "action": "retention_purge",
                    "status": "sessions_deleted",
                    "expired_sessions_deleted": expired_sessions_deleted
                }}
            )

        result = {
            'accounts_deleted': accounts_deleted,
            'inactive_accounts_deleted': inactive_accounts_deleted,
            'expired_sessions_deleted': expired_sessions_deleted,
        }
        self.logger.info(
            "Retention purge completed",
            extra={"context": {
                "action": "retention_purge",
                "status": "success",
                **result
            }}
        )
        return result

    def _delete_account(self, user: UserDB) -> None:
        """Delete a user's account with all of its personal data.

        The personal data is deleted explicitly before the user row
        so the purge also works on databases without foreign-key
        cascade enforcement (e.g. SQLite without the foreign_keys
        pragma). When the user requested revocation with the account
        deletion, the user's shared correction contributions are
        withdrawn first (GDPR Art. 7(3)); the user row must still
        exist for the link cascade.

        Args:
            user: User entity to delete.
        """
        user_id = cast(int, user.id)
        if user.revoke_shared_corrections:
            withdrawn = (
                self.shared_correction_repository.withdraw_by_user_id(
                    user_id
                )
            )
            self.logger.info(
                "Shared correction contributions withdrawn",
                extra={"context": {
                    "action": "retention_purge",
                    "status": "contributions_withdrawn",
                    "user_id": user_id,
                    "contributions_withdrawn": withdrawn
                }}
            )
        else:
            # The user linkage is personal data and is removed with
            # the account; the anonymized shared corrections remain.
            self.shared_correction_repository.delete_links_by_user_id(
                user_id
            )
        self.transaction_repository.delete_by_user_id(user_id)
        self.correction_repository.delete_by_user_id(user_id)
        self.processing_result_repository.delete_by_user_id(user_id)
        self.session_repository.revoke_by_user_id(user_id)
        self.user_repository.delete(user_id)

    def _purge_due_deletions(self, now: datetime) -> int:
        """Delete accounts whose grace period has elapsed.

        Args:
            now: Current UTC timestamp.

        Returns:
            Number of accounts deleted.
        """
        due_users = self.user_repository.find_due_for_deletion(now)
        for user in due_users:
            self._delete_account(user)
            self.logger.info(
                "Account deleted after grace period",
                extra={"context": {
                    "action": "retention_purge",
                    "status": "account_deleted",
                    "user_id": user.id
                }}
            )
        return len(due_users)

    def _purge_inactive_users(self, now: datetime) -> int:
        """Delete the accounts of inactive users.

        Deletes the account and its personal data of users whose last
        activity is older than the inactivity window. The deletion is
        permanent; a returning user must register a new account.
        Shared corrections of inactive users are anonymized and are
        retained (no revocation was requested).

        Args:
            now: Current UTC timestamp.

        Returns:
            Number of accounts deleted.
        """
        cutoff = now - timedelta(days=self.inactivity_days)
        inactive_users = self.user_repository.find_inactive_since(cutoff)
        for user in inactive_users:
            self._delete_account(user)
            self.logger.info(
                "Account deleted after inactivity",
                extra={"context": {
                    "action": "retention_purge",
                    "status": "account_deleted",
                    "reason": "inactivity",
                    "user_id": user.id
                }}
            )
        return len(inactive_users)


def create_retention_service_from_app(app: Any) -> RetentionService:
    """Build a RetentionService from a Flask application's extensions.

    Args:
        app: Flask application with repositories and services
            registered in its extensions dictionary.

    Returns:
        Configured RetentionService instance.
    """
    from whatsthedamage.config.auth_config import get_auth_config

    auth_config = get_auth_config()
    return RetentionService(
        user_repository=app.extensions['user_repository'],
        session_repository=app.extensions['session_repository'],
        password_service=app.extensions['password_service'],
        transaction_repository=app.extensions[
            'transaction_repository'
        ],
        correction_repository=app.extensions['correction_repository'],
        processing_result_repository=app.extensions[
            'processing_result_repository'
        ],
        shared_correction_repository=app.extensions[
            'shared_correction_repository'
        ],
        deletion_grace_days=auth_config.ACCOUNT_DELETION_GRACE_DAYS,
        inactivity_days=auth_config.RETENTION_INACTIVITY_DAYS
    )
