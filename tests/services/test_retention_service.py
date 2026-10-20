"""Tests for RetentionService.

Tests account deletion scheduling and the periodic purge of personal
data (see docs/retention-policy.md). The account purge runs through a
unit of work, so the tests mock the unit of work factory.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, Mock

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
    return mock


@pytest.fixture
def mock_session_repository():
    """Create a mock SessionRepository for testing."""
    mock = Mock()
    mock.cleanup_expired_and_revoked.return_value = 0
    return mock


@pytest.fixture
def mock_unit_of_work():
    """Create a mock SqlAlchemyUnitOfWork.

    purge_user runs in the mock's context manager; purge_user returns
    counts matching the service's logging expectations.
    """
    uow = Mock()
    uow.purge_user.return_value = {
        'contribution_links_deleted': 0,
        'transactions_deleted': 0,
        'corrections_deleted': 0,
        'processing_results_deleted': 0,
        'sessions_revoked': 0,
    }
    uow_cm = MagicMock()
    uow_cm.__enter__.return_value = uow
    return uow_cm


@pytest.fixture
def retention_service(
    mock_user_repository,
    mock_session_repository,
    password_service,
    mock_unit_of_work,
    monkeypatch
):
    """Create a RetentionService instance with a mocked unit of work."""

    def _uow_factory(_session_factory):
        return mock_unit_of_work

    monkeypatch.setattr(
        'whatsthedamage.services.retention_service.SqlAlchemyUnitOfWork',
        _uow_factory
    )
    return RetentionService(
        user_repository=mock_user_repository,
        session_repository=mock_session_repository,
        password_service=password_service,
        session_factory=Mock(),
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
            1, scheduled_at, revoke_shared_corrections=False
        )
        mock_session_repository.revoke_by_user_id.assert_called_once_with(1)

    def test_schedules_deletion_with_shared_correction_revocation(
        self, retention_service, mock_user_repository, user
    ):
        """The revocation option is persisted with the request."""
        retention_service.request_account_deletion(
            user, 'password-123456', revoke_shared_corrections=True
        )

        mock_user_repository.schedule_deletion.assert_called_once_with(
            mock_user_repository.schedule_deletion.call_args[0][0],
            mock_user_repository.schedule_deletion.call_args[0][1],
            revoke_shared_corrections=True
        )

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
        mock_session_repository, mock_unit_of_work, user
    ):
        """Accounts past their grace period are fully deleted."""
        mock_user_repository.find_due_for_deletion.return_value = [user]

        result = retention_service.purge()

        assert result == {
            'accounts_deleted': 1,
            'inactive_accounts_deleted': 0,
            'expired_sessions_deleted': 0
        }
        uow = mock_unit_of_work.__enter__.return_value
        uow.purge_user.assert_called_once_with(
            1, revoke_shared_corrections=False
        )
        uow.commit.assert_called_once_with()

    def test_purge_keeps_pending_accounts(
        self, retention_service, mock_user_repository,
        mock_unit_of_work, user
    ):
        """Accounts still inside the grace period are not deleted."""
        mock_user_repository.find_due_for_deletion.return_value = []

        result = retention_service.purge()

        assert result['accounts_deleted'] == 0
        mock_unit_of_work.__enter__.return_value.purge_user \
            .assert_not_called()

    def test_purge_deletes_inactive_users_account(
        self, retention_service, mock_user_repository,
        mock_session_repository, mock_unit_of_work, user
    ):
        """Inactive users' accounts are permanently deleted."""
        mock_user_repository.find_inactive_since.return_value = [user]

        result = retention_service.purge()

        assert result == {
            'accounts_deleted': 0,
            'inactive_accounts_deleted': 1,
            'expired_sessions_deleted': 0
        }
        uow = mock_unit_of_work.__enter__.return_value
        uow.purge_user.assert_called_once_with(
            1, revoke_shared_corrections=False
        )
        uow.commit.assert_called_once_with()

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

    def test_purge_deletes_expired_sessions(
        self, retention_service, mock_session_repository
    ):
        """Expired and revoked session rows are physically deleted."""
        mock_session_repository.cleanup_expired_and_revoked.return_value = 3

        result = retention_service.purge()

        mock_session_repository.cleanup_expired_and_revoked \
            .assert_called_once_with()
        assert result['expired_sessions_deleted'] == 3

    def test_purge_withdraws_shared_corrections_on_request(
        self, retention_service, mock_user_repository,
        mock_unit_of_work, user
    ):
        """Contributions are withdrawn when the user requested it."""
        user.revoke_shared_corrections = True
        mock_user_repository.find_due_for_deletion.return_value = [user]

        retention_service.purge()

        uow = mock_unit_of_work.__enter__.return_value
        uow.purge_user.assert_called_once_with(
            1, revoke_shared_corrections=True
        )

    def test_purge_keeps_shared_corrections_without_request(
        self, retention_service, mock_user_repository,
        mock_unit_of_work, user
    ):
        """Without a revocation request the linkage is deleted only."""
        user.revoke_shared_corrections = False
        mock_user_repository.find_due_for_deletion.return_value = [user]

        retention_service.purge()

        uow = mock_unit_of_work.__enter__.return_value
        uow.purge_user.assert_called_once_with(
            1, revoke_shared_corrections=False
        )
