"""Tests for the SqlAlchemyUnitOfWork.

Verifies that multi-entity writes through the unit of work are atomic:
commit persists everything together and a failure persists nothing.
Also covers the batched deduplication hash lookup.
"""

import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from whatsthedamage.models.database.base import Base
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.transaction import Transaction as TransactionDB
from whatsthedamage.models.database.processing_result import ProcessingResult as ProcessingResultDB
from whatsthedamage.models.database.correction import Correction as CorrectionDB  # noqa: F401
from whatsthedamage.models.database.shared_correction import SharedCorrection as SharedCorrectionDB  # noqa: F401
from whatsthedamage.models.repositories.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def db_session_factory():
    """Create a session factory bound to an in-memory SQLite database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session
    engine.dispose()


def _create_user(session_factory) -> int:
    """Create a user row and return its identifier."""
    session = session_factory()
    try:
        user = UserDB(
            username='uow-user',
            password_hash='hash',
            recovery_code_hash='hash',
            created_at=datetime.now(UTC)
        )
        session.add(user)
        session.commit()
        return user.id
    finally:
        session.close()


def _make_result(user_id: int, result_id: str = 'result-1') -> ProcessingResultDB:
    """Create a ProcessingResult entity for testing."""
    return ProcessingResultDB(
        result_id=result_id,
        user_id=user_id,
        csv_profile_id=None,
        row_count=2,
        processing_time=0.1,
        ml_enabled=False,
        created_at=datetime.now(UTC)
    )


def _make_transaction(
    user_id: int,
    result_id: str,
    dedup_hash: str,
    amount: float = -1.0
) -> TransactionDB:
    """Create a Transaction entity for testing."""
    return TransactionDB(
        user_id=user_id,
        result_id=result_id,
        date=datetime(2026, 1, 15, tzinfo=UTC),
        transaction_type='debit',
        original_partner='TEST MERCHANT',
        amount=amount,
        currency='EUR',
        account='main',
        deduplication_hash=dedup_hash,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


class TestSqlAlchemyUnitOfWork:
    """Tests for atomic multi-entity writes."""

    def test_commit_persists_result_and_transactions(self, db_session_factory):
        """Test Cases:
            Both the processing result and its transactions are visible
            together after a single commit.
        """
        user_id = _create_user(db_session_factory)
        result = _make_result(user_id)
        transactions = [
            _make_transaction(user_id, result.result_id, 'hash-1'),
            _make_transaction(user_id, result.result_id, 'hash-2'),
        ]

        with SqlAlchemyUnitOfWork(db_session_factory) as uow:
            uow.processing_results.add(result)
            uow.transactions.add_all(transactions)
            uow.commit()

        check_session = db_session_factory()
        try:
            stored_result = check_session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == 'result-1'
            ).one()
            stored_count = check_session.query(TransactionDB).filter(
                TransactionDB.result_id == 'result-1'
            ).count()
            assert stored_result.row_count == 2
            assert stored_count == 2
        finally:
            check_session.close()

    def test_exception_rolls_back_everything(self, db_session_factory):
        """Test Cases:
            An exception inside the unit of work leaves neither the
            processing result nor any transaction behind.
        """
        user_id = _create_user(db_session_factory)
        result = _make_result(user_id, 'result-rollback')
        transactions = [
            _make_transaction(user_id, result.result_id, 'hash-r1'),
        ]

        with pytest.raises(RuntimeError):
            with SqlAlchemyUnitOfWork(db_session_factory) as uow:
                uow.processing_results.add(result)
                uow.transactions.add_all(transactions)
                raise RuntimeError('boom')

        check_session = db_session_factory()
        try:
            assert check_session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == 'result-rollback'
            ).count() == 0
            assert check_session.query(TransactionDB).filter(
                TransactionDB.result_id == 'result-rollback'
            ).count() == 0
        finally:
            check_session.close()

    def test_uncommitted_writes_are_discarded_on_exit(self, db_session_factory):
        """Test Cases:
            Leaving the unit of work without committing discards all
            pending writes.
        """
        user_id = _create_user(db_session_factory)
        result = _make_result(user_id, 'result-nocommit')

        with SqlAlchemyUnitOfWork(db_session_factory) as uow:
            uow.processing_results.add(result)
            uow.transactions.add_all([
                _make_transaction(user_id, result.result_id, 'hash-n1'),
            ])

        check_session = db_session_factory()
        try:
            assert check_session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == 'result-nocommit'
            ).count() == 0
            assert check_session.query(TransactionDB).count() == 0
        finally:
            check_session.close()


class TestFindExistingDedupHashes:
    """Tests for the batched deduplication hash lookup."""

    def test_returns_only_existing_hashes(self, db_session_factory):
        """Test Cases:
            Only hashes present in the database are returned; unknown
            hashes are absent from the result.
        """
        user_id = _create_user(db_session_factory)
        result = _make_result(user_id, 'result-dedup')

        with SqlAlchemyUnitOfWork(db_session_factory) as uow:
            uow.processing_results.add(result)
            uow.transactions.add_all([
                _make_transaction(user_id, result.result_id, 'hash-a'),
                _make_transaction(user_id, result.result_id, 'hash-b'),
            ])
            uow.commit()

        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        repo = SqlAlchemyTransactionRepository(db_session_factory)
        existing = repo.find_existing_dedup_hashes(
            ['hash-a', 'hash-b', 'hash-c', 'hash-d']
        )
        assert existing == {'hash-a', 'hash-b'}

    def test_chunks_large_hash_lists(self, db_session_factory):
        """Test Cases:
            Hash lists longer than one query chunk still find matches
            located in later chunks.
        """
        user_id = _create_user(db_session_factory)
        result = _make_result(user_id, 'result-chunked')
        seeded_hash = f'hash-{600:04d}'

        with SqlAlchemyUnitOfWork(db_session_factory) as uow:
            uow.processing_results.add(result)
            uow.transactions.add_all([
                _make_transaction(user_id, result.result_id, seeded_hash),
            ])
            uow.commit()

        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        repo = SqlAlchemyTransactionRepository(db_session_factory)
        all_hashes = [f'hash-{i:04d}' for i in range(601)]
        existing = repo.find_existing_dedup_hashes(all_hashes)
        assert existing == {seeded_hash}

    def test_empty_hash_list_returns_empty_set(self, db_session_factory):
        """Test Cases:
            An empty input list returns an empty set without querying.
        """
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        repo = SqlAlchemyTransactionRepository(db_session_factory)
        assert repo.find_existing_dedup_hashes([]) == set()
