"""Tests for RetentionService.

Tests account deletion scheduling and the periodic purge of personal
data (see docs/retention-policy.md).
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock

from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.services.password_service import PasswordService
from whatsthedamage.services.retention_service import RetentionService


@pytest.fixture
def password_service():
    """Create a real PasswordService for password verification."""
    return PasswordService(time_cost=2, memory_cost=16384, parallelism=1)


@pytest.fixture
def user(password_service):
    """Create a user entity with a known password."""
    return UserDB(
        id=1,
        username='alice',
        password_hash=password_service.hash_password('password-123456'),
        recovery_code_hash=password_service.hash_password('CODE'),
        is_active=True
    )


@pytest.fixture
def mock_user_repository():
    """Create a mock UserRepository for testing."""
    mock = Mock()
    mock.find_due_for_deletion.return_value = []
    mock.find_inactive_since.return_value = []
    mock.schedule_deletion.return_value = True
    mock.cancel_deletion.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_session_repository():
    """Create a mock SessionRepository for testing."""
    return Mock()


@pytest.fixture
def mock_transaction_repository():
    """Create a mock TransactionRepository for testing."""
    mock = Mock()
    mock.delete_by_user_id.return_value = 0
    return mock


@pytest.fixture
def mock_correction_repository():
    """Create a mock CorrectionRepository for testing."""
    mock = Mock()
    mock.delete_by_user_id.return_value = 0
    return mock


@pytest.fixture
def mock_processing_result_repository():
    """Create a mock ProcessingResultRepository for testing."""
    mock = Mock()
    mock.delete_by_user_id.return_value = 0
    return mock


@pytest.fixture
def retention_service(
    mock_user_repository,
    mock_session_repository,
    password_service,
    mock_transaction_repository,
    mock_correction_repository,
    mock_processing_result_repository
):
    """Create a RetentionService instance for testing."""
    return RetentionService(
        user_repository=mock_user_repository,
        session_repository=mock_session_repository,
        password_service=password_service,
        transaction_repository=mock_transaction_repository,
        correction_repository=mock_correction_repository,
        processing_result_repository=mock_processing_result_repository,
        deletion_grace_days=7,
        inactivity_days=180
    )


class TestRequestAccountDeletion:
    """Tests for scheduling account deletion."""

    def test_schedules_deletion_after_grace_period(
        self, retention_service, mock_user_repository,
        mock_session_repository, user
    ):
        """A valid request schedules deletion and revokes sessions."""
        before = datetime.now(UTC)

        scheduled_at = retention_service.request_account_deletion(
            user, 'password-123456'
        )

        after = datetime.now(UTC) + timedelta(days=7)
        assert before + timedelta(days=7) <= scheduled_at <= after
        mock_user_repository.schedule_deletion.assert_called_once_with(
            1, scheduled_at
        )
        mock_session_repository.revoke_by_user_id.assert_called_once_with(1)

    def test_wrong_password_raises(
        self, retention_service, mock_user_repository,
        mock_session_repository, user
    ):
        """A wrong password raises and schedules nothing."""
        with pytest.raises(ValueError, match="Invalid password"):
            retention_service.request_account_deletion(
                user, 'wrong-password'
            )

        mock_user_repository.schedule_deletion.assert_not_called()
        mock_session_repository.revoke_by_user_id.assert_not_called()


class TestPurge:
    """Tests for the periodic purge job."""

    def test_purge_deletes_due_accounts(
        self, retention_service, mock_user_repository,
        mock_session_repository, user
    ):
        """Accounts past their grace period are fully deleted."""
        mock_user_repository.find_due_for_deletion.return_value = [user]

        result = retention_service.purge()

        assert result == {
            'accounts_deleted': 1,
            'inactive_accounts_deleted': 0
        }
        mock_user_repository.delete.assert_called_once_with(1)
        mock_session_repository.revoke_by_user_id.assert_called_once_with(1)

    def test_purge_keeps_pending_accounts(
        self, retention_service, mock_user_repository, user
    ):
        """Accounts still inside the grace period are not deleted."""
        mock_user_repository.find_due_for_deletion.return_value = []

        result = retention_service.purge()

        assert result['accounts_deleted'] == 0
        mock_user_repository.delete.assert_not_called()

    def test_purge_deletes_inactive_users_account(
        self, retention_service, mock_user_repository,
        mock_session_repository, mock_transaction_repository,
        mock_correction_repository, mock_processing_result_repository,
        user
    ):
        """Inactive users' accounts are permanently deleted."""
        mock_user_repository.find_inactive_since.return_value = [user]

        result = retention_service.purge()

        assert result == {
            'accounts_deleted': 0,
            'inactive_accounts_deleted': 1
        }
        mock_user_repository.delete.assert_called_once_with(1)
        mock_session_repository.revoke_by_user_id.assert_called_once_with(1)
        mock_transaction_repository.delete_by_user_id.assert_called_once_with(1)
        mock_correction_repository.delete_by_user_id.assert_called_once_with(1)
        mock_processing_result_repository.delete_by_user_id. \
            assert_called_once_with(1)

    def test_purge_uses_inactivity_cutoff(
        self, retention_service, mock_user_repository
    ):
        """The inactivity window drives the cutoff timestamp."""
        before = datetime.now(UTC)
        retention_service.purge()
        after = datetime.now(UTC)

        cutoff = mock_user_repository.find_inactive_since.call_args[0][0]
        expected_min = before - timedelta(days=180)
        expected_max = after - timedelta(days=180)
        assert expected_min <= cutoff <= expected_max

    def test_purge_never_touches_shared_corrections(
        self, retention_service, mock_user_repository, user
    ):
        """Shared corrections have no user linkage and are not queried."""
        mock_user_repository.find_due_for_deletion.return_value = [user]

        retention_service.purge()

        # The retention service has no shared correction repository;
        # the purge only goes through user, transaction, correction,
        # and processing result repositories.
        assert not hasattr(retention_service, 'shared_correction_repository')
