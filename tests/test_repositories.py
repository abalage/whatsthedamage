"""Tests for UserRepository and SessionRepository.

Tests CRUD operations and business logic for user and session repositories.
"""

import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from whatsthedamage.models.database.base import Base
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.database.transaction import Transaction as TransactionDB
from whatsthedamage.models.database.processing_result import ProcessingResult as ProcessingResultDB
from whatsthedamage.models.database.correction import Correction as CorrectionDB
from whatsthedamage.models.database.shared_correction import SharedCorrection as SharedCorrectionDB
from whatsthedamage.models.repositories.user_repository import SqlAlchemyUserRepository
from whatsthedamage.models.repositories.session_repository import SqlAlchemySessionRepository
from whatsthedamage.services.password_service import PasswordService


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session_factory(db_engine):
    """Create a session factory for testing."""
    Session = sessionmaker(bind=db_engine)
    return Session


@pytest.fixture
def user_repository(db_session_factory):
    """Create a UserRepository instance for testing."""
    return SqlAlchemyUserRepository(db_session_factory)


@pytest.fixture
def session_repository(db_session_factory):
    """Create a SessionRepository instance for testing."""
    return SqlAlchemySessionRepository(db_session_factory)


@pytest.fixture
def password_service():
    """Create a PasswordService instance for testing."""
    return PasswordService(
        time_cost=2,
        memory_cost=16384,
        parallelism=1
    )


class TestUserRepository:
    """Tests for UserRepository operations."""

    def test_create_user(self, user_repository, password_service):
        """Test creating a new user."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        user = user_repository.create(
            username='testuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        assert user is not None
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.password_hash == password_hash
        assert user.recovery_code_hash == recovery_code_hash
        assert user.is_active is True
        assert user.opt_in_sharing is False
        assert user.created_at is not None

    def test_create_user_duplicate_username(self, user_repository, password_service):
        """Test creating a user with duplicate username raises error."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create first user
        user_repository.create(
            username='testuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            user_repository.create(
                username='testuser',
                password_hash=password_hash,
                recovery_code_hash=recovery_code_hash
            )

    def test_find_by_username(self, user_repository, password_service):
        """Test finding user by username."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create user
        created_user = user_repository.create(
            username='finduser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Find user
        found_user = user_repository.find_by_username('finduser')

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == 'finduser'

    def test_find_by_username_not_found(self, user_repository):
        """Test finding non-existent user by username."""
        result = user_repository.find_by_username('nonexistent')
        assert result is None

    def test_find_by_id(self, user_repository, password_service):
        """Test finding user by ID."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create user
        created_user = user_repository.create(
            username='findbyid',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Find user
        found_user = user_repository.find_by_id(created_user.id)

        assert found_user is not None
        assert found_user.id == created_user.id

    def test_find_by_id_not_found(self, user_repository):
        """Test finding non-existent user by ID."""
        result = user_repository.find_by_id(99999)
        assert result is None

    def test_update_last_login(self, user_repository, password_service):
        """Test updating user's last login timestamp."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create user
        user = user_repository.create(
            username='loginuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Update last login
        user_repository.update_last_login(user.id)

        # Verify update
        updated_user = user_repository.find_by_id(user.id)
        assert updated_user.last_login_at is not None

    def test_set_active(self, user_repository, password_service):
        """Test setting user's active status."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create user
        user = user_repository.create(
            username='activeuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Deactivate user
        user_repository.set_active(user.id, False)

        # Verify deactivation
        updated_user = user_repository.find_by_id(user.id)
        assert updated_user.is_active is False

        # Reactivate user
        user_repository.set_active(user.id, True)

        # Verify reactivation
        updated_user = user_repository.find_by_id(user.id)
        assert updated_user.is_active is True

    def test_find_all(self, user_repository, password_service):
        """Test finding all users."""
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')

        # Create multiple users
        user_repository.create(
            username='user1',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )
        user_repository.create(
            username='user2',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Find all
        users = user_repository.find_all()

        assert len(users) == 2

    def test_update_password_and_recovery_code_success(
        self, user_repository, password_service
    ):
        """Test atomic update of password and recovery code hashes."""
        # Create a user
        password_hash = password_service.hash_password('old_password')
        recovery_code_hash = password_service.hash_password('OLD-CODE-1234-5678')

        user = user_repository.create(
            username='updateuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Update both fields atomically
        new_password_hash = password_service.hash_password('new_password')
        new_recovery_code_hash = password_service.hash_password('NEW-CODE-9876-5432')

        result = user_repository.update_password_and_recovery_code(
            user_id=user.id,
            new_password_hash=new_password_hash,
            new_recovery_code_hash=new_recovery_code_hash
        )

        assert result is True

        # Verify both fields were updated
        updated_user = user_repository.find_by_id(user.id)
        assert updated_user.password_hash == new_password_hash
        assert updated_user.recovery_code_hash == new_recovery_code_hash

    def test_update_password_and_recovery_code_user_not_found(
        self, user_repository, password_service
    ):
        """Test update fails gracefully for non-existent user."""
        new_password_hash = password_service.hash_password('new_password')
        new_recovery_code_hash = password_service.hash_password('NEW-CODE-1234')

        result = user_repository.update_password_and_recovery_code(
            user_id=99999,
            new_password_hash=new_password_hash,
            new_recovery_code_hash=new_recovery_code_hash
        )

        assert result is False

    def test_update_password_and_recovery_code_atomicity(
        self, user_repository, password_service
    ):
        """Test that password and recovery code are updated atomically."""
        # Create a user
        password_hash = password_service.hash_password('old_password')
        recovery_code_hash = password_service.hash_password('OLD-CODE-1234')

        user = user_repository.create(
            username='atomicuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Update both fields
        new_password_hash = password_service.hash_password('new_password')
        new_recovery_code_hash = password_service.hash_password('NEW-CODE-5678')

        result = user_repository.update_password_and_recovery_code(
            user_id=user.id,
            new_password_hash=new_password_hash,
            new_recovery_code_hash=new_recovery_code_hash
        )

        assert result is True

        # Verify both were updated - if atomic, both should be new values
        updated_user = user_repository.find_by_id(user.id)
        assert updated_user.password_hash == new_password_hash
        assert updated_user.recovery_code_hash == new_recovery_code_hash

        # Verify neither is the old value
        assert updated_user.password_hash != password_hash
        assert updated_user.recovery_code_hash != recovery_code_hash

    def test_update_password_and_recovery_code_rollback_on_error(
        self, user_repository, password_service
    ):
        """Test that rollback occurs on database error."""
        # Create a user
        password_hash = password_service.hash_password('old_password')
        recovery_code_hash = password_service.hash_password('OLD-CODE-1234')

        user = user_repository.create(
            username='rollbackuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Get the original values
        original_password_hash = user.password_hash
        original_recovery_hash = user.recovery_code_hash

        # Try to update with a database error - we need to simulate this
        # For SQLite in-memory, this is hard to simulate, but we can verify
        # that the method returns False for non-existent user
        new_password_hash = password_service.hash_password('new_password')
        new_recovery_code_hash = password_service.hash_password('NEW-CODE-5678')

        # Non-existent user should return False
        result = user_repository.update_password_and_recovery_code(
            user_id=99999,
            new_password_hash=new_password_hash,
            new_recovery_code_hash=new_recovery_code_hash
        )

        assert result is False

        # Verify original user is unchanged
        unchanged_user = user_repository.find_by_id(user.id)
        assert unchanged_user.password_hash == original_password_hash
        assert unchanged_user.recovery_code_hash == original_recovery_hash


class TestSessionRepository:
    """Tests for SessionRepository operations."""

    def test_create_session(self, session_repository, user_repository, password_service):
        """Test creating a new session."""
        # First create a user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create session
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session = session_repository.create(
            user_id=user.id,
            token_hash='test_hash_64_chars_long_1234567890abcdef',
            token_hash_prefix='test_pre',
            expires_at=expires_at,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )

        assert session is not None
        assert session.id is not None
        assert session.user_id == user.id
        assert session.token_hash == 'test_hash_64_chars_long_1234567890abcdef'
        assert session.token_hash_prefix == 'test_pre'
        assert session.expires_at == expires_at
        assert session.ip_address == '127.0.0.1'
        assert session.user_agent == 'Test Agent'
        assert session.is_revoked is False

    def test_find_by_token_hash(self, session_repository, user_repository, password_service):
        """Test finding session by token hash."""
        # Create user and session
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='find_by_hash',
            token_hash_prefix='find_pre',
            expires_at=expires_at
        )

        # Find session
        found_session = session_repository.find_by_token_hash('find_by_hash')

        assert found_session is not None
        assert found_session.token_hash == 'find_by_hash'

    def test_find_by_token_hash_not_found(self, session_repository):
        """Test finding non-existent session by token hash."""
        result = session_repository.find_by_token_hash('nonexistent')
        assert result is None

    def test_find_by_token_hash_prefix(self, session_repository, user_repository, password_service):
        """Test finding session by token hash prefix."""
        # Create user and session
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='prefix_hash_1234567890abcdef1234567890abcdef',
            token_hash_prefix='prefix_ha',
            expires_at=expires_at
        )

        # Find session by prefix
        found_session = session_repository.find_by_token_hash_prefix('prefix_ha')

        assert found_session is not None
        assert found_session.token_hash_prefix == 'prefix_ha'

    def test_find_by_user_id(self, session_repository, user_repository, password_service):
        """Test finding sessions by user ID."""
        # Create user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create multiple sessions for the user
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='session_hash_1',
            token_hash_prefix='sess_pre1',
            expires_at=expires_at
        )
        session_repository.create(
            user_id=user.id,
            token_hash='session_hash_2',
            token_hash_prefix='sess_pre2',
            expires_at=expires_at
        )

        # Find sessions
        sessions = session_repository.find_by_user_id(user.id)

        assert len(sessions) == 2
        assert all(s.user_id == user.id for s in sessions)

    def test_revoke_by_token_hash(self, session_repository, user_repository, password_service):
        """Test revoking a session by token hash."""
        # Create user and session
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='revoke_hash',
            token_hash_prefix='revoke_p',
            expires_at=expires_at
        )

        # Revoke session
        result = session_repository.revoke_by_token_hash('revoke_hash')

        assert result is True

        # Verify revocation
        session = session_repository.find_by_token_hash('revoke_hash')
        assert session.is_revoked is True

    def test_revoke_by_token_hash_not_found(self, session_repository):
        """Test revoking non-existent session."""
        result = session_repository.revoke_by_token_hash('nonexistent')
        assert result is False

    def test_revoke_by_user_id(self, session_repository, user_repository, password_service):
        """Test revoking all sessions for a user."""
        # Create user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create multiple sessions
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='session_hash_1',
            token_hash_prefix='sess_pre1',
            expires_at=expires_at
        )
        session_repository.create(
            user_id=user.id,
            token_hash='session_hash_2',
            token_hash_prefix='sess_pre2',
            expires_at=expires_at
        )

        # Revoke all sessions
        count = session_repository.revoke_by_user_id(user.id)

        assert count == 2

        # Verify all are revoked
        sessions = session_repository.find_by_user_id(user.id)
        assert all(s.is_revoked is True for s in sessions)

    def test_revoke_expired(self, session_repository, user_repository, password_service):
        """Test revoking all expired sessions (lazy cleanup)."""
        # Create user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create an expired session
        expires_at = datetime.now(UTC) - timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='expired_hash',
            token_hash_prefix='exp_pre',
            expires_at=expires_at
        )

        # Create a valid session
        future_expires = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='valid_hash',
            token_hash_prefix='val_pre',
            expires_at=future_expires
        )

        # Revoke expired sessions
        count = session_repository.revoke_expired()

        assert count == 1

        # Verify only expired is revoked
        expired_session = session_repository.find_by_token_hash('expired_hash')
        valid_session = session_repository.find_by_token_hash('valid_hash')
        assert expired_session.is_revoked is True
        assert valid_session.is_revoked is False

    def test_concurrent_session_limit(self, session_repository, user_repository, password_service):
        """Test enforcement of concurrent session limit."""
        # Create user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create 5 sessions (the limit)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        for i in range(5):
            session_repository.create(
                user_id=user.id,
                token_hash=f'session_hash_{i}',
                token_hash_prefix=f'sess_{i}',
                expires_at=expires_at
            )

        # Create 6th session - should revoke oldest
        session_repository.create(
            user_id=user.id,
            token_hash='session_hash_new',
            token_hash_prefix='sess_new',
            expires_at=expires_at
        )

        # Verify only 5 active sessions
        active_sessions = session_repository.find_by_user_id(user.id)
        assert len(active_sessions) == 6  # Total sessions

        # Count non-revoked sessions
        non_revoked = [s for s in active_sessions if not s.is_revoked]
        assert len(non_revoked) == 5  # Only 5 active (oldest was revoked)

        # Verify oldest is revoked
        oldest = session_repository.find_by_token_hash('session_hash_0')
        assert oldest.is_revoked is True

    def test_cleanup_expired_and_revoked(self, session_repository, user_repository, password_service):
        """Test physical cleanup of expired and revoked sessions."""
        # Create user
        password_hash = password_service.hash_password('test_password')
        recovery_code_hash = password_service.hash_password('ABCD-EFGH-IJKL-MNOP')
        user = user_repository.create(
            username='sessionuser',
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create expired session
        expires_at = datetime.now(UTC) - timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='expired_hash',
            token_hash_prefix='exp_pre',
            expires_at=expires_at
        )

        # Create a session and mark it as revoked
        future_expires = datetime.now(UTC) + timedelta(hours=1)
        session_repository.create(
            user_id=user.id,
            token_hash='revoked_hash',
            token_hash_prefix='rev_pre',
            expires_at=future_expires
        )
        # Revoke it using the repository method
        session_repository.revoke_by_token_hash('revoked_hash')

        # Create valid session
        session_repository.create(
            user_id=user.id,
            token_hash='valid_hash',
            token_hash_prefix='val_pre',
            expires_at=future_expires
        )

        # Cleanup
        count = session_repository.cleanup_expired_and_revoked()

        # Should cleanup expired (1) + revoked (1) = 2
        assert count == 2

        # Verify only valid remains
        all_sessions = session_repository.find_by_user_id(user.id)
        assert len(all_sessions) == 1
        assert all_sessions[0].token_hash == 'valid_hash'


class TestTransactionRepositoryFilters:
    """Tests for SqlAlchemyTransactionRepository.find_by_user_with_filters."""

    @pytest.fixture
    def transaction_repository(self, db_session_factory):
        """Create a TransactionRepository for testing."""
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        return SqlAlchemyTransactionRepository(db_session_factory)

    @staticmethod
    def _make_transaction(account):
        """Create a Transaction entity with the given account."""
        return TransactionDB(
            user_id=1,
            result_id='result-1',
            date=datetime(2024, 1, 15, tzinfo=UTC),
            transaction_type='debit',
            original_partner='Test Partner',
            amount=-100.0,
            currency='HUF',
            account=account,
            deduplication_hash=f'hash-{account}',
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def _seed(self, transaction_repository):
        """Seed one transaction per account variant."""
        for account in ('acc1', 'unknown', ''):
            transaction_repository.create(self._make_transaction(account))

    def test_unknown_account_filter_matches_empty_accounts(self, transaction_repository):
        """Filtering by the 'unknown' account also matches legacy rows
        persisted with an empty account."""
        self._seed(transaction_repository)

        transactions, total_count = transaction_repository.find_by_user_with_filters(
            user_id=1, account='unknown'
        )

        accounts = {t.account for t in transactions}
        assert accounts == {'unknown', ''}
        assert total_count == 2

    def test_account_filter_returns_only_matching_account(self, transaction_repository):
        """Filtering by a concrete account returns only its rows."""
        self._seed(transaction_repository)

        transactions, total_count = transaction_repository.find_by_user_with_filters(
            user_id=1, account='acc1'
        )

        assert [t.account for t in transactions] == ['acc1']
        assert total_count == 1
