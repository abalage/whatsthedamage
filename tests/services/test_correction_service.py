"""Tests for CorrectionService.

Tests correction saving, retrieval, application, and deletion functionality.
"""

import pytest
from unittest.mock import Mock

from whatsthedamage.services.correction_service import CorrectionService
from tests.utils.transaction_test_factory import TransactionTestFactory


class TestCorrectionService:
    """Tests for CorrectionService."""

    @pytest.fixture
    def mock_correction_repo(self):
        """Create a mock correction repository."""
        repo = Mock()
        repo.find_by_user_and_original_partner = Mock(return_value=None)
        repo.create = Mock()
        repo.update = Mock(return_value=True)
        repo.delete = Mock(return_value=True)
        repo.find_by_user_id = Mock(return_value=[])
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        """Create a mock transaction repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_correction_repo, mock_transaction_repo):
        """Create a CorrectionService instance with mock repositories."""
        return CorrectionService(mock_correction_repo, mock_transaction_repo)

    def test_save_new_correction(self, service, mock_correction_repo):
        """Test saving a new correction."""
        user_id = 1
        original_partner = "TEST PARTNER"
        corrected_partner = "CORRECTED PARTNER"

        mock_correction_repo.find_by_user_and_original_partner.return_value = None
        mock_correction_repo.create.return_value = Mock()

        correction = service.save_correction(
            user_id,
            original_partner,
            corrected_partner=corrected_partner
        )

        assert correction is not None
        mock_correction_repo.create.assert_called_once()

    def test_update_existing_correction(self, service, mock_correction_repo):
        """Test updating an existing correction."""
        user_id = 1
        original_partner = "TEST PARTNER"
        corrected_partner = "CORRECTED PARTNER"
        corrected_category_id = "CATEGORY001"

        existing_correction = Mock()
        existing_correction.id = 1
        mock_correction_repo.find_by_user_and_original_partner.return_value = existing_correction
        mock_correction_repo.update.return_value = True

        correction = service.save_correction(
            user_id,
            original_partner,
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id
        )

        assert correction == existing_correction
        mock_correction_repo.update.assert_called_once()

    def test_apply_corrections_to_row_with_correction(self, service, mock_correction_repo):
        """Test applying corrections to a CSV row when correction exists."""
        user_id = 1
        csv_row = TransactionTestFactory.create_csv_row(partner="TEST PARTNER")

        correction = Mock()
        correction.corrected_partner = "CORRECTED PARTNER"
        correction.corrected_category_id = "CATEGORY001"
        correction.corrected_notice = "NOTICE"
        mock_correction_repo.find_by_user_and_original_partner.return_value = correction

        corrected_row = service.apply_corrections_to_row(user_id, csv_row)

        assert corrected_row.partner == "CORRECTED PARTNER"
        assert corrected_row.category_id == "CATEGORY001"
        assert corrected_row.notice == "NOTICE"

    def test_apply_corrections_to_row_without_correction(self, service, mock_correction_repo):
        """Test applying corrections to a CSV row when no correction exists."""
        user_id = 1
        csv_row = TransactionTestFactory.create_csv_row(partner="TEST PARTNER")

        mock_correction_repo.find_by_user_and_original_partner.return_value = None

        corrected_row = service.apply_corrections_to_row(user_id, csv_row)

        assert corrected_row == csv_row

    def test_apply_corrections_to_rows(self, service, mock_correction_repo):
        """Test applying corrections to multiple CSV rows."""
        user_id = 1
        csv_rows = [
            TransactionTestFactory.create_csv_row(partner="PARTNER 1"),
            TransactionTestFactory.create_csv_row(partner="PARTNER 2"),
            TransactionTestFactory.create_csv_row(partner="PARTNER 3"),
        ]

        # Only PARTNER 2 has a correction
        def find_correction(user_id, partner):
            if partner == "PARTNER 2":
                correction = Mock()
                correction.corrected_partner = "CORRECTED PARTNER 2"
                return correction
            return None

        mock_correction_repo.find_by_user_and_original_partner.side_effect = find_correction

        corrected_rows = service.apply_corrections_to_rows(user_id, csv_rows)

        assert len(corrected_rows) == 3
        assert corrected_rows[0].partner == "PARTNER 1"
        assert corrected_rows[1].partner == "CORRECTED PARTNER 2"
        assert corrected_rows[2].partner == "PARTNER 3"

    def test_get_correction(self, service, mock_correction_repo):
        """Test getting a correction by original_partner."""
        user_id = 1
        original_partner = "TEST PARTNER"

        correction = Mock()
        mock_correction_repo.find_by_user_and_original_partner.return_value = correction

        result = service.get_correction(user_id, original_partner)

        assert result == correction
        mock_correction_repo.find_by_user_and_original_partner.assert_called_once_with(
            user_id, original_partner
        )

    def test_get_correction_not_found(self, service, mock_correction_repo):
        """Test getting a correction that doesn't exist."""
        user_id = 1
        original_partner = "NONEXISTENT PARTNER"

        mock_correction_repo.find_by_user_and_original_partner.return_value = None

        result = service.get_correction(user_id, original_partner)

        assert result is None

    def test_delete_correction(self, service, mock_correction_repo):
        """Test deleting a correction."""
        user_id = 1
        original_partner = "TEST PARTNER"

        correction = Mock()
        correction.id = 1
        mock_correction_repo.find_by_user_and_original_partner.return_value = correction
        mock_correction_repo.delete.return_value = True

        result = service.delete_correction(user_id, original_partner)

        assert result is True
        mock_correction_repo.delete.assert_called_once()

    def test_delete_correction_not_found(self, service, mock_correction_repo):
        """Test deleting a correction that doesn't exist."""
        user_id = 1
        original_partner = "NONEXISTENT PARTNER"

        mock_correction_repo.find_by_user_and_original_partner.return_value = None

        result = service.delete_correction(user_id, original_partner)

        assert result is False
        mock_correction_repo.delete.assert_not_called()

    def test_get_all_corrections(self, service, mock_correction_repo):
        """Test getting all corrections for a user."""
        user_id = 1

        corrections = [Mock(), Mock(), Mock()]
        mock_correction_repo.find_by_user_id.return_value = corrections

        result = service.get_all_corrections(user_id)

        assert result == corrections
        mock_correction_repo.find_by_user_id.assert_called_once_with(user_id)
