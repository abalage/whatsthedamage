"""Tests for TransactionPersistenceService.

Tests transaction saving, deduplication, and correction application functionality.
"""

import pytest
from unittest.mock import Mock, patch

from whatsthedamage.services.transaction_persistence_service import (
    TransactionPersistenceService
)
from whatsthedamage.services.deduplication_service import DeduplicationService
from tests.utils.transaction_test_factory import TransactionTestFactory


class TestTransactionPersistenceService:
    """Tests for TransactionPersistenceService."""

    @pytest.fixture
    def mock_transaction_repo(self):
        """Create a mock transaction repository."""
        repo = Mock()
        repo.find_by_dedup_hash = Mock(return_value=None)
        repo.create = Mock()
        return repo

    @pytest.fixture
    def mock_correction_repo(self):
        """Create a mock correction repository."""
        repo = Mock()
        repo.find_by_user_and_original_partner = Mock(return_value=None)
        return repo

    @pytest.fixture
    def service(self, mock_transaction_repo, mock_correction_repo):
        """Create a TransactionPersistenceService instance with mock repositories."""
        return TransactionPersistenceService(
            mock_transaction_repo, mock_correction_repo
        )

    @pytest.fixture
    def dedup_service(self):
        """Create a DeduplicationService instance."""
        return DeduplicationService()

    def test_save_new_transaction(self, service, mock_transaction_repo, dedup_service):
        """Test saving a new transaction."""
        csv_row = TransactionTestFactory.create_csv_row()
        user_id = 1

        mock_transaction_repo.find_by_dedup_hash.return_value = None
        mock_transaction_repo.create.return_value = Mock()

        transaction, is_new = service.save_transaction(
            user_id, csv_row, dedup_service
        )

        assert is_new is True
        mock_transaction_repo.find_by_dedup_hash.assert_called_once()
        mock_transaction_repo.create.assert_called_once()

    def test_save_duplicate_transaction(self, service, mock_transaction_repo, dedup_service):
        """Test that duplicate transactions are not saved twice."""
        csv_row = TransactionTestFactory.create_csv_row()
        user_id = 1

        existing_transaction = Mock()
        mock_transaction_repo.find_by_dedup_hash.return_value = existing_transaction

        transaction, is_new = service.save_transaction(
            user_id, csv_row, dedup_service
        )

        assert is_new is False
        assert transaction == existing_transaction
        mock_transaction_repo.create.assert_not_called()

    def test_save_with_corrections(self, service, mock_transaction_repo, dedup_service):
        """Test saving a transaction with corrections applied."""
        csv_row = TransactionTestFactory.create_csv_row()
        user_id = 1

        corrected_partner = "CORRECTED PARTNER"
        corrected_category_id = "CORRECTED_CATEGORY"
        corrected_notice = "CORRECTED NOTICE"

        mock_transaction_repo.find_by_dedup_hash.return_value = None
        mock_transaction_repo.create.return_value = Mock()

        transaction, is_new = service.save_transaction(
            user_id,
            csv_row,
            dedup_service,
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id,
            corrected_notice=corrected_notice
        )

        assert is_new is True
        call_args = mock_transaction_repo.create.call_args[0][0]
        assert call_args.partner == corrected_partner
        assert call_args.category_id == corrected_category_id
        assert call_args.notice == corrected_notice

    def test_save_transactions_from_csv(self, service, mock_transaction_repo, dedup_service):
        """Test saving multiple transactions from CSV."""
        user_id = 1
        csv_rows = [
            TransactionTestFactory.create_csv_row(date="2024-01-01"),
            TransactionTestFactory.create_csv_row(date="2024-01-02"),
            TransactionTestFactory.create_csv_row(date="2024-01-03"),
        ]

        mock_transaction_repo.find_by_dedup_hash.return_value = None
        mock_transaction_repo.create.return_value = Mock()

        saved_transactions, new_count = service.save_transactions_from_csv(
            user_id, csv_rows, dedup_service
        )

        assert len(saved_transactions) == 3
        assert new_count == 3
        assert mock_transaction_repo.create.call_count == 3

    def test_save_transactions_with_duplicates(self, service, mock_transaction_repo, dedup_service):
        """Test that duplicate transactions are skipped when saving from CSV."""
        user_id = 1
        csv_row = TransactionTestFactory.create_csv_row()
        csv_rows = [csv_row, csv_row, csv_row]  # Same row 3 times

        # First call returns None (no duplicate), subsequent calls return existing
        mock_transaction_repo.find_by_dedup_hash.side_effect = [None, Mock(), Mock()]
        mock_transaction_repo.create.return_value = Mock()

        saved_transactions, new_count = service.save_transactions_from_csv(
            user_id, csv_rows, dedup_service
        )

        assert new_count == 1
        assert mock_transaction_repo.create.call_count == 1

    def test_get_transactions_for_user(self, service, mock_transaction_repo):
        """Test getting transactions for a user."""
        user_id = 1
        limit = 100
        offset = 0

        mock_transactions = [Mock(), Mock()]
        mock_transaction_repo.find_by_user_id.return_value = mock_transactions

        result = service.get_transactions_for_user(user_id, limit, offset)

        # get_transactions_for_user returns (transactions, count)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == mock_transactions
        mock_transaction_repo.find_by_user_id.assert_called_once_with(
            user_id, limit, offset
        )
