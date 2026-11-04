"""Tests for the authentication services.

Tests account operations (AccountService: registration, login,
password reset, opt-in sharing) and the session lifecycle
(AuthSessionService: logout, session validation, CSRF).
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, MagicMock, patch

from whatsthedamage.services.account_service import AccountService
from whatsthedamage.services.auth_errors import (
    InvalidCredentialsError,
    UsernameExistsError,
)
from whatsthedamage.services.auth_session_service import AuthSessionService
from whatsthedamage.services.password_service import PasswordService
from whatsthedamage.services.token_service import TokenService
from whatsthedamage.services.recovery_code_service import RecoveryCodeService
from whatsthedamage.services.csrf_service import CsrfService


@pytest.fixture
def mock_user_repository():
    """Create a mock UserRepository for testing."""
    mock = Mock()
    mock.find_by_username.return_value = None
    # Login and password reset look up confirmed users only; alias the
    # same mock so tests can stub either name
    mock.find_confirmed_by_username = mock.find_by_username
    mock.find_by_id.return_value = None
    mock.create.return_value = Mock(id=1, username='testuser')
    mock.create_pending.return_value = Mock(id=1, username='testuser')
    mock.find_pending_by_token_hash.return_value = None
    mock.confirm_pending.return_value = True
    mock.delete_expired_pending.return_value = 0
    mock.update_last_login.return_value = None
    return mock


@pytest.fixture
def mock_session_repository():
    """Create a mock SessionRepository for testing."""
    mock = Mock()
    mock.create.return_value = Mock(
        id=1,
        user_id=1,
        token_hash='test_hash',
        token_hash_prefix='test_pre',
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_revoked=False
    )
    mock.find_by_token_hash.return_value = None
    mock.find_by_user_id.return_value = []
    mock.find_active_by_user_id.return_value = []
    mock.revoke_by_token_hash.return_value = True
    mock.revoke_by_user_id.return_value = 1
    return mock


@pytest.fixture
def mock_recovery_code_service():
    """Create a mock RecoveryCodeService for testing."""
    mock = Mock()
    mock.generate_code.return_value = 'ABCDEFGHJKLMNPQR'
    mock.format_code.return_value = 'ABCD-EFGH-JKLM-NPQR'
    # parse_code must actually parse so wrong echoed codes fail verification
    mock.parse_code.side_effect = RecoveryCodeService().parse_code
    return mock


@pytest.fixture
def auth_session_service(mock_user_repository, mock_session_repository):
    """Create an AuthSessionService instance for testing."""
    return AuthSessionService(
        user_repository=mock_user_repository,
        session_repository=mock_session_repository,
        token_service=TokenService(),
        csrf_service=CsrfService(),
        session_timeout=3600,
        remember_me_duration=604800,
        max_concurrent_sessions=5
    )


@pytest.fixture
def account_service(
    auth_session_service, mock_user_repository, mock_recovery_code_service
):
    """Create an AccountService instance for testing."""
    return AccountService(
        user_repository=mock_user_repository,
        password_service=PasswordService(
            time_cost=2,
            memory_cost=16384,
            parallelism=1
        ),
        recovery_code_service=mock_recovery_code_service,
        session_service=auth_session_service,
        token_service=TokenService(),
        password_min_length=12,
        pending_ttl_seconds=1800
    )


class TestAccountServiceRegistration:
    """Tests for two-phase registration (pending + confirm)."""

    def test_create_pending_registration_success(
        self, account_service, mock_user_repository, mock_session_repository
    ):
        """Phase 1 creates a pending row but no session."""
        mock_user_repository.find_by_username.return_value = None
        mock_user_repository.create_pending.return_value = Mock(
            id=1,
            username='newuser',
            created_at=datetime.now(UTC)
        )

        pending_token, recovery_code, expires_at = (
            account_service.create_pending_registration(
                username='newuser',
                password='secure_password_1234',
                ip_address='127.0.0.1',
                user_agent='Test Agent'
            )
        )

        assert len(pending_token) > 0
        assert recovery_code == 'ABCD-EFGH-JKLM-NPQR'
        assert expires_at > datetime.now(UTC)
        assert mock_user_repository.create_pending.called
        # No session is created at phase 1
        assert not mock_session_repository.create.called
        # Only the token hash is passed to the repository
        call_kwargs = mock_user_repository.create_pending.call_args.kwargs
        assert call_kwargs['pending_token_hash'] != pending_token
        assert len(call_kwargs['pending_token_hash']) == 64

    def test_create_pending_registration_confirmed_username_taken(
        self, account_service, mock_user_repository
    ):
        """A confirmed account holding the username blocks registration."""
        mock_user_repository.find_by_username.return_value = Mock(
            id=1,
            username='existing',
            registration_confirmed_at=datetime.now(UTC)
        )

        with pytest.raises(UsernameExistsError, match="already exists"):
            account_service.create_pending_registration(
                username='existing',
                password='secure_password_1234'
            )

    def test_create_pending_registration_unexpired_pending_taken(
        self, account_service, mock_user_repository
    ):
        """An unexpired pending registration holding the username blocks."""
        mock_user_repository.find_by_username.return_value = Mock(
            id=1,
            username='existing',
            registration_confirmed_at=None
        )
        mock_user_repository.create_pending.side_effect = ValueError(
            "Username 'existing' already exists"
        )

        with pytest.raises(UsernameExistsError, match="already exists"):
            account_service.create_pending_registration(
                username='existing',
                password='secure_password_1234'
            )

    def test_create_pending_registration_empty_username(self, account_service):
        """Test registration with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            account_service.create_pending_registration(
                username='',
                password='secure_password_1234'
            )

    def test_create_pending_registration_long_username(self, account_service):
        """Test registration with username exceeding 255 characters."""
        with pytest.raises(ValueError, match="cannot exceed 255 characters"):
            account_service.create_pending_registration(
                username='a' * 256,
                password='secure_password_1234'
            )

    def test_create_pending_registration_short_password(self, account_service):
        """Test registration with password too short."""
        with pytest.raises(ValueError, match="Password must be at least 12 characters"):
            account_service.create_pending_registration(
                username='newuser',
                password='short'
            )

    def _pending_user_mock(self):
        """Build a pending user mock whose recovery code hash matches the mock service."""
        password_service = PasswordService(
            time_cost=2, memory_cost=16384, parallelism=1
        )
        return Mock(
            id=1,
            username='newuser',
            recovery_code_hash=password_service.hash_password('ABCDEFGHJKLMNPQR')
        )

    def test_confirm_registration_success(
        self, account_service, mock_user_repository, mock_session_repository
    ):
        """Phase 2 with the correct echoed code commits the account and creates a session."""
        pending_user = self._pending_user_mock()
        mock_user_repository.find_pending_by_token_hash.return_value = pending_user
        mock_user_repository.confirm_pending.return_value = True
        mock_user_repository.find_by_id.return_value = Mock(
            id=1,
            username='newuser',
            created_at=datetime.now(UTC)
        )

        user, session_token, session_expiry, csrf_token = (
            account_service.confirm_registration(
                pending_token='the-pending-token',
                recovery_code='ABCD-EFGH-JKLM-NPQR',
                ip_address='127.0.0.1',
                user_agent='Test Agent'
            )
        )

        assert user.username == 'newuser'
        assert len(session_token) > 0
        assert session_expiry > datetime.now(UTC)
        assert len(csrf_token) > 0
        assert mock_user_repository.confirm_pending.called
        assert mock_session_repository.create.called
        assert account_service.session_service.validate_csrf_token(
            csrf_token,
            mock_session_repository.create.call_args.kwargs['csrf_token_hash']
        )

    def test_confirm_registration_wrong_code(
        self, account_service, mock_user_repository, mock_session_repository
    ):
        """Phase 2 with a mismatched recovery code is rejected and commits nothing."""
        mock_user_repository.find_pending_by_token_hash.return_value = (
            self._pending_user_mock()
        )

        with pytest.raises(InvalidCredentialsError):
            account_service.confirm_registration(
                pending_token='the-pending-token',
                recovery_code='XXXX-XXXX-XXXX-XXXX'
            )

        assert not mock_user_repository.confirm_pending.called
        assert not mock_session_repository.create.called

    def test_confirm_registration_unknown_or_expired_token(self, account_service):
        """Phase 2 with an unknown/expired token is rejected."""
        mock_user_repository = account_service.user_repository
        mock_user_repository.find_pending_by_token_hash.return_value = None

        with pytest.raises(InvalidCredentialsError):
            account_service.confirm_registration(
                pending_token='no-such-token',
                recovery_code='ABCD-EFGH-JKLM-NPQR'
            )

    def test_confirm_registration_race_loses(
        self, account_service, mock_user_repository, mock_session_repository
    ):
        """When the guarded confirm update loses a race, no session is created."""
        mock_user_repository.find_pending_by_token_hash.return_value = (
            self._pending_user_mock()
        )
        mock_user_repository.confirm_pending.return_value = False

        with pytest.raises(InvalidCredentialsError):
            account_service.confirm_registration(
                pending_token='the-pending-token',
                recovery_code='ABCD-EFGH-JKLM-NPQR'
            )

        assert not mock_session_repository.create.called


class TestAccountServiceLogin:
    """Tests for user login functionality."""

    def test_login_user_success(self, account_service, mock_user_repository, mock_session_repository):
        """Test successful user login."""
        # Setup mock user
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True,
            last_login_at=None,
            scheduled_deletion_at=None
        )
        mock_user_repository.find_by_username.return_value = mock_user

        # Mock password verification
        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            user, session_token, session_expiry, csrf_token = (
                account_service.login_user(
                    username='testuser',
                    password='correct_password',
                    remember_me=False,
                    ip_address='127.0.0.1',
                    user_agent='Test Agent'
                )
            )

        assert user is not None
        assert user.username == 'testuser'
        assert len(session_token) > 0
        assert session_expiry > datetime.now(UTC)
        assert len(csrf_token) > 0
        assert mock_user_repository.update_last_login.called
        assert mock_session_repository.create.called
        # The returned token must match the hash persisted with the session
        assert account_service.session_service.validate_csrf_token(
            csrf_token,
            mock_session_repository.create.call_args.kwargs['csrf_token_hash']
        )

    def test_login_user_invalid_username(self, account_service, mock_user_repository):
        """Test login with invalid username."""
        mock_user_repository.find_by_username.return_value = None

        with pytest.raises(ValueError, match="Invalid username or password"):
            account_service.login_user(
                username='nonexistent',
                password='some_password'
            )

    def test_login_user_invalid_password(self, account_service, mock_user_repository):
        """Test login with invalid password."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=False
        ):
            with pytest.raises(ValueError, match="Invalid username or password"):
                account_service.login_user(
                    username='testuser',
                    password='wrong_password'
                )

    def test_login_user_inactive_account(self, account_service, mock_user_repository):
        """Test login with inactive account."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=False
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            with pytest.raises(ValueError, match="Account is inactive"):
                account_service.login_user(
                    username='testuser',
                    password='correct_password'
                )

    def test_login_user_cancels_pending_deletion(
        self, account_service, mock_user_repository
    ):
        """Logging in during the grace period cancels the deletion."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True,
            scheduled_deletion_at=datetime.now(UTC) + timedelta(days=3)
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            account_service.login_user(
                username='testuser',
                password='correct_password'
            )

        mock_user_repository.cancel_deletion.assert_called_once_with(1)
        assert mock_user_repository.update_last_login.called

    def test_login_user_refuses_past_due_deletion(
        self, account_service, mock_user_repository
    ):
        """Login is refused once the scheduled deletion has elapsed."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True,
            scheduled_deletion_at=datetime.now(UTC) - timedelta(days=1)
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            with pytest.raises(
                ValueError,
                match="Account is scheduled for deletion"
            ):
                account_service.login_user(
                    username='testuser',
                    password='correct_password'
                )

        mock_user_repository.cancel_deletion.assert_not_called()
        mock_user_repository.update_last_login.assert_not_called()

    def test_login_user_without_scheduled_deletion_skips_cancel(
        self, account_service, mock_user_repository
    ):
        """Regular logins never call the deletion cancel."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True,
            scheduled_deletion_at=None
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            account_service.login_user(
                username='testuser',
                password='correct_password'
            )

        mock_user_repository.cancel_deletion.assert_not_called()

    def test_login_user_remember_me(self, account_service, mock_user_repository, mock_session_repository):
        """Test login with remember me option."""
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$v=19$m=65536,t=3,p=4$...',
            is_active=True,
            scheduled_deletion_at=None
        )
        mock_user_repository.find_by_username.return_value = mock_user

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            with patch.object(
                account_service.session_service.token_service,
                'generate_token_and_hash',
                return_value=('token', 'hash')
            ):
                user, session_token, session_expiry, csrf_token = (
                    account_service.login_user(
                        username='testuser',
                        password='correct_password',
                        remember_me=True,
                        ip_address='127.0.0.1',
                        user_agent='Test Agent'
                    )
                )

                # Remember me should use 7 days expiration
                expected_expiry = datetime.now(UTC) + timedelta(days=7)
                # Allow for small time differences
                time_diff = abs((session_expiry - expected_expiry).total_seconds())
                assert time_diff < 5, f"Session expiry not set to 7 days, diff: {time_diff}s"


class TestAccountServiceConcurrentSessionLimit:
    """Tests for the concurrent session limit business rule."""

    def test_login_revokes_oldest_sessions_beyond_limit(
        self, account_service, mock_user_repository,
        mock_session_repository
    ):
        """Test Cases:
            Creating a session beyond the limit revokes the oldest
            active sessions; the configured limit is honored.
        """
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$...',
            is_active=True,
            last_login_at=None,
            scheduled_deletion_at=None
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_session_repository.find_active_by_user_id.return_value = [
            Mock(id=i) for i in range(5)
        ]

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            account_service.login_user(
                username='testuser',
                password='correct_password'
            )

        mock_session_repository.revoke_by_ids.assert_called_once_with([0])
        assert mock_session_repository.create.called

    def test_login_within_limit_does_not_revoke(
        self, account_service, mock_user_repository,
        mock_session_repository
    ):
        """Test Cases:
            Creating a session when the user is below the limit
            revokes nothing.
        """
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash='$argon2id$...',
            is_active=True,
            last_login_at=None,
            scheduled_deletion_at=None
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_session_repository.find_active_by_user_id.return_value = [
            Mock(id=i) for i in range(3)
        ]

        with patch.object(
            account_service.password_service,
            'verify_password',
            return_value=True
        ):
            account_service.login_user(
                username='testuser',
                password='correct_password'
            )

        mock_session_repository.revoke_by_ids.assert_not_called()


class TestAuthSessionServiceLogout:
    """Tests for user logout functionality."""

    def test_logout_user_success(self, auth_session_service, mock_session_repository):
        """Test successful user logout."""
        mock_session_repository.revoke_by_token_hash.return_value = True

        result = auth_session_service.logout_user('valid_token')

        assert result is True
        assert mock_session_repository.revoke_by_token_hash.called

    def test_logout_user_invalid_session(self, auth_session_service, mock_session_repository):
        """Test logout with invalid session."""
        mock_session_repository.revoke_by_token_hash.return_value = False

        result = auth_session_service.logout_user('invalid_token')

        assert result is False

    def test_logout_all_user_sessions(self, auth_session_service, mock_session_repository):
        """Test logout all sessions for a user."""
        mock_session_repository.revoke_by_user_id.return_value = 3

        result = auth_session_service.logout_all_user_sessions(1)

        assert result == 3


class TestAuthSessionServiceSessionValidation:
    """Tests for session validation functionality."""

    def test_validate_session_success(self, auth_session_service, mock_session_repository, mock_user_repository):
        """Test successful session validation."""
        mock_user = Mock(id=1, username='testuser', is_active=True)
        mock_session = Mock(
            id=1,
            user_id=1,
            token_hash='test_hash',
            is_revoked=False,
            expires_at=datetime.now(UTC) + timedelta(hours=1)
        )

        mock_session_repository.find_by_token_hash.return_value = mock_session
        mock_user_repository.find_by_id.return_value = mock_user

        with patch.object(
            auth_session_service.token_service,
            'hash_token',
            return_value='test_hash'
        ):
            result = auth_session_service.validate_session('valid_token')

        assert result is not None
        user, session = result
        assert user.id == 1
        assert session.id == 1

    def test_validate_session_invalid_token(self, auth_session_service, mock_session_repository):
        """Test session validation with invalid token."""
        mock_session_repository.find_by_token_hash.return_value = None

        with patch.object(
            auth_session_service.token_service,
            'hash_token',
            return_value='invalid_hash'
        ):
            result = auth_session_service.validate_session('invalid_token')

        assert result is None

    def test_validate_session_revoked(self, auth_session_service, mock_session_repository):
        """Test session validation with revoked session."""
        mock_session = Mock(
            id=1,
            user_id=1,
            is_revoked=True,
            expires_at=datetime.now(UTC) + timedelta(hours=1)
        )
        mock_session_repository.find_by_token_hash.return_value = mock_session

        with patch.object(
            auth_session_service.token_service,
            'hash_token',
            return_value='test_hash'
        ):
            result = auth_session_service.validate_session('valid_token')

        assert result is None

    def test_validate_session_expired(self, auth_session_service, mock_session_repository):
        """Test session validation with expired session."""
        mock_session = Mock(
            id=1,
            user_id=1,
            is_revoked=False,
            expires_at=datetime.now(UTC) - timedelta(hours=1)
        )
        mock_session_repository.find_by_token_hash.return_value = mock_session

        with patch.object(
            auth_session_service.token_service,
            'hash_token',
            return_value='test_hash'
        ):
            result = auth_session_service.validate_session('valid_token')

        assert result is None

    def test_validate_session_inactive_user(self, auth_session_service, mock_session_repository, mock_user_repository):
        """Test session validation with inactive user."""
        mock_session = Mock(
            id=1,
            user_id=1,
            is_revoked=False,
            expires_at=datetime.now(UTC) + timedelta(hours=1)
        )
        mock_user = Mock(id=1, is_active=False)

        mock_session_repository.find_by_token_hash.return_value = mock_session
        mock_user_repository.find_by_id.return_value = mock_user

        with patch.object(
            auth_session_service.token_service,
            'hash_token',
            return_value='test_hash'
        ):
            result = auth_session_service.validate_session('valid_token')

        assert result is None


class TestAuthSessionServiceCsrf:
    """Tests for CSRF token functionality."""

    def test_validate_csrf_token(self, auth_session_service):
        """Test CSRF token validation."""
        csrf_token, csrf_token_hash = CsrfService().generate_token_and_hash()

        assert auth_session_service.validate_csrf_token(csrf_token, csrf_token_hash) is True
        assert auth_session_service.validate_csrf_token('invalid', csrf_token_hash) is False


class TestAuthSessionServiceCsrfRefresh:
    """Tests for refreshing CSRF tokens."""

    def test_refresh_csrf_token_persists_hash(
        self, auth_session_service, mock_session_repository
    ):
        """Test refresh_csrf_token returns a token whose hash is stored."""
        mock_session = Mock(id=1, csrf_token_hash=None)

        csrf_token = auth_session_service.refresh_csrf_token(mock_session)

        assert len(csrf_token) > 0
        mock_session_repository.update_csrf_token_hash.assert_called_once()
        stored_hash = mock_session_repository.update_csrf_token_hash.call_args[0][1]
        assert auth_session_service.validate_csrf_token(csrf_token, stored_hash)
        assert mock_session.csrf_token_hash == stored_hash


class TestAccountServicePasswordReset:
    """Tests for password reset using recovery code functionality."""

    def test_reset_password_with_recovery_code_success(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test successful password reset with valid recovery code."""
        # Setup mock user with recovery code hash
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)
        password_hash = password_service.hash_password('old_password')

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        # Reset password
        user, new_formatted_recovery_code = account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCD-EFGH-JKLM-NPQR',
            new_password='new_secure_password_1234'
        )

        assert user is not None
        assert user.id == 1
        assert new_formatted_recovery_code == '2NEW-ABCD-3EFG-HJKL'
        assert mock_user_repository.update_password_and_recovery_code.called
        assert mock_session_repository.revoke_by_user_id.called
        assert mock_user_repository.update_last_login.called

    def test_reset_password_with_recovery_code_invalid_username(
        self, account_service, mock_user_repository
    ):
        """Test password reset with invalid username."""
        mock_user_repository.find_by_username.return_value = None

        with pytest.raises(ValueError, match="Invalid username or recovery code"):
            account_service.reset_password_with_recovery_code(
                username='nonexistent',
                recovery_code='ABCD-EFGH-JKLM-NPQR',
                new_password='new_secure_password_1234'
            )

    def test_reset_password_with_recovery_code_invalid_recovery_code(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """Test password reset with invalid recovery code."""
        password_service = account_service.password_service

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=password_service.hash_password('DIFFERENT-CODE'),
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_recovery_code_service.parse_code.return_value = 'WRONG-CODE-ABCD'

        with pytest.raises(ValueError, match="Invalid username or recovery code"):
            account_service.reset_password_with_recovery_code(
                username='testuser',
                recovery_code='WRONG-CODE',
                new_password='new_secure_password_1234'
            )

    def test_reset_password_with_recovery_code_short_password(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """Test password reset with password too short."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw

        with pytest.raises(ValueError, match="Password must be at least 12 characters"):
            account_service.reset_password_with_recovery_code(
                username='testuser',
                recovery_code='ABCD-EFGH-JKLM-NPQR',
                new_password='short'
            )

    def test_reset_password_with_recovery_code_regenerates_code(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test that a new recovery code is generated after password reset."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        user, new_formatted_recovery_code = account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCD-EFGH-JKLM-NPQR',
            new_password='new_secure_password_1234'
        )

        # Verify new recovery code was generated
        assert mock_recovery_code_service.generate_code.called
        assert new_formatted_recovery_code == '2NEW-ABCD-3EFG-HJKL'

    def test_reset_password_with_recovery_code_invalidates_sessions(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test that all user sessions are invalidated on password reset."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_session_repository.revoke_by_user_id.return_value = 3
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCD-EFGH-JKLM-NPQR',
            new_password='new_secure_password_1234'
        )

        # Verify session invalidation was called
        mock_session_repository.revoke_by_user_id.assert_called_once_with(1)

    def test_reset_password_with_recovery_code_formatted_input(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test password reset accepts formatted recovery code with hyphens."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        # Call with formatted recovery code (with hyphens)
        user, new_formatted_recovery_code = account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCD-EFGH-JKLM-NPQR',
            new_password='new_secure_password_1234'
        )

        # Verify parse_code was called to normalize the input
        mock_recovery_code_service.parse_code.assert_called_once()
        assert user is not None

    def test_reset_password_with_recovery_code_unformatted_input(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test password reset accepts unformatted recovery code without hyphens."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )
        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        # Call with unformatted recovery code (no hyphens)
        user, new_formatted_recovery_code = account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCDEFGHJKLMNPQR',
            new_password='new_secure_password_1234'
        )

        assert user is not None
        assert new_formatted_recovery_code == '2NEW-ABCD-3EFG-HJKL'

    def test_reset_password_with_recovery_code_old_code_invalidated(
        self, account_service, mock_user_repository, mock_session_repository, mock_recovery_code_service
    ):
        """Test that old recovery code is invalidated after password reset."""
        password_service = account_service.password_service
        old_recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        old_recovery_code_hash = password_service.hash_password(old_recovery_code_raw)
        password_hash = password_service.hash_password('old_password')

        # Create mock user with old recovery code
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_hash,
            recovery_code_hash=old_recovery_code_hash,
            is_active=True
        )
        # Store the original recovery code hash for later verification
        original_recovery_hash = old_recovery_code_hash

        mock_user_repository.find_by_username.return_value = mock_user
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.update_password_and_recovery_code.return_value = True
        mock_recovery_code_service.parse_code.return_value = old_recovery_code_raw
        mock_recovery_code_service.generate_code.return_value = '2NEWABCD3EFGHJKL'
        mock_recovery_code_service.format_code.return_value = '2NEW-ABCD-3EFG-HJKL'

        # Reset password
        user, new_formatted_recovery_code = account_service.reset_password_with_recovery_code(
            username='testuser',
            recovery_code='ABCD-EFGH-JKLM-NPQR',
            new_password='new_secure_password_1234'
        )

        # Verify update was called with new hashes
        assert mock_user_repository.update_password_and_recovery_code.called
        call_args = mock_user_repository.update_password_and_recovery_code.call_args
        new_recovery_hash = call_args[1]['new_recovery_code_hash']

        # Old recovery code should no longer work
        assert new_recovery_hash != original_recovery_hash

        # Verify that the old code would not match the new hash
        # (simulating verification with old code)
        assert not password_service.verify_password(old_recovery_code_raw, new_recovery_hash)

    def test_reset_password_with_recovery_code_update_failed(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """Test that appropriate error is raised when update fails."""
        password_service = account_service.password_service
        recovery_code_raw = 'ABCDEFGHJKLMNPQR'
        recovery_code_hash = password_service.hash_password(recovery_code_raw)

        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('old_password'),
            recovery_code_hash=recovery_code_hash,
            is_active=True
        )

        mock_user_repository.find_by_username.return_value = mock_user
        # Update returns False (user not found or database error)
        mock_user_repository.update_password_and_recovery_code.return_value = False
        mock_recovery_code_service.parse_code.return_value = recovery_code_raw

        with pytest.raises(ValueError, match="Invalid username or recovery code"):
            account_service.reset_password_with_recovery_code(
                username='testuser',
                recovery_code='ABCD-EFGH-JKLM-NPQR',
                new_password='new_secure_password_1234'
            )


class TestAccountServiceUpdateOptInSharing:
    """Tests for updating the sharing opt-in preference."""

    def test_update_opt_in_sharing_returns_updated_user(
        self, account_service, mock_user_repository
    ):
        """Updating the preference returns the reloaded user."""
        updated_user = Mock(id=1, username='testuser', opt_in_sharing=True)
        mock_user_repository.set_opt_in_sharing.return_value = True
        mock_user_repository.find_by_id.return_value = updated_user

        result = account_service.update_opt_in_sharing(1, True)

        assert result is updated_user
        mock_user_repository.set_opt_in_sharing.assert_called_once_with(1, True)
        mock_user_repository.find_by_id.assert_called_once_with(1)

    def test_update_opt_in_sharing_revocation(
        self, account_service, mock_user_repository
    ):
        """Revoking the opt-in persists False."""
        updated_user = Mock(id=1, username='testuser', opt_in_sharing=False)
        mock_user_repository.set_opt_in_sharing.return_value = True
        mock_user_repository.find_by_id.return_value = updated_user

        result = account_service.update_opt_in_sharing(1, False)

        assert result is updated_user
        mock_user_repository.set_opt_in_sharing.assert_called_once_with(1, False)

    def test_update_opt_in_sharing_user_not_found(
        self, account_service, mock_user_repository
    ):
        """When the repository cannot find the user, None is returned."""
        mock_user_repository.set_opt_in_sharing.return_value = False

        result = account_service.update_opt_in_sharing(99999, True)

        assert result is None
        mock_user_repository.find_by_id.assert_not_called()


class TestRegenerateRecoveryCode:
    """Tests for AccountService.regenerate_recovery_code."""

    def test_success_returns_formatted_code(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """Valid password returns the new formatted recovery code."""
        password_service = account_service.password_service
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('correct-password'),
            recovery_code_hash=password_service.hash_password('OLD-CODE'),
            is_active=True
        )
        mock_current_session = Mock(id=42)
        mock_user_repository.update_credentials.return_value = True
        mock_recovery_code_service.generate_code.return_value = 'NEWRAWCODE123456'
        mock_recovery_code_service.format_code.return_value = 'NEWR-AWCO-DE12-3456'

        result = account_service.regenerate_recovery_code(
            mock_user, 'correct-password', mock_current_session
        )

        assert result == 'NEWR-AWCO-DE12-3456'
        mock_user_repository.update_credentials.assert_called_once()
        call_kwargs = mock_user_repository.update_credentials.call_args
        assert call_kwargs.kwargs.get('new_recovery_code_hash') is not None
        assert call_kwargs.kwargs.get('new_password_hash') is None

    def test_revokes_other_sessions(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """All sessions except the current one are revoked."""
        password_service = account_service.password_service
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('correct-password'),
            recovery_code_hash=password_service.hash_password('OLD-CODE'),
            is_active=True
        )
        mock_current_session = Mock(id=42)
        mock_user_repository.update_credentials.return_value = True

        with patch.object(
            account_service.session_service, 'revoke_all_sessions_except',
            return_value=2
        ) as mock_revoke:
            account_service.regenerate_recovery_code(
                mock_user, 'correct-password', mock_current_session
            )

        mock_revoke.assert_called_once_with(1, 42)

    def test_wrong_password_raises(
        self, account_service, mock_user_repository
    ):
        """A wrong password raises InvalidPasswordError."""
        from whatsthedamage.services.auth_errors import InvalidPasswordError

        password_service = account_service.password_service
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('correct-password'),
            recovery_code_hash=password_service.hash_password('OLD-CODE'),
            is_active=True
        )
        mock_current_session = Mock(id=42)

        with pytest.raises(InvalidPasswordError):
            account_service.regenerate_recovery_code(
                mock_user, 'wrong-password', mock_current_session
            )

        mock_user_repository.update_credentials.assert_not_called()

    def test_repository_update_failure_raises(
        self, account_service, mock_user_repository, mock_recovery_code_service
    ):
        """When the repository update fails, ValueError is raised."""
        password_service = account_service.password_service
        mock_user = Mock(
            id=1,
            username='testuser',
            password_hash=password_service.hash_password('correct-password'),
            recovery_code_hash=password_service.hash_password('OLD-CODE'),
            is_active=True
        )
        mock_current_session = Mock(id=42)
        mock_user_repository.update_credentials.return_value = False

        with pytest.raises(ValueError, match="User not found"):
            account_service.regenerate_recovery_code(
                mock_user, 'correct-password', mock_current_session
            )
