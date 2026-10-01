"""Functional tests for upload-time correction application (US-5).

Verifies that corrections bound to the authenticated user are applied to
newly uploaded transactions via a case-insensitive exact match on
original_partner, that the deduplication key stays immutable when
corrections are applied, that corrections owned by other users are
ignored, and that re-uploads keep existing corrected transactions.
"""

from typing import Any
from unittest.mock import MagicMock

from tests.api_test_utils import MockProcessingService

CSRF_HEADERS = {'X-CSRF-Token': 'test_csrf_token'}

def _upload(
    client: Any,
    mock_processing_service: MagicMock,
    merchant: str,
    amount: float = 100.0,
    category: str = 'grocery',
    amounts: list[float] | None = None,
) -> Any:
    """Upload a CSV yielding transactions with the given merchant.

    Each call configures a fresh mock result so repeated uploads in one
    test get distinct processing result IDs. ``amounts`` yields one
    transaction per amount; otherwise a single transaction with
    ``amount`` is yielded.
    """
    from tests.api_test_utils import create_csv_bytes
    totals = amounts if amounts is not None else [amount]
    details = [
        MockProcessingService.create_detail_row(category, total, merchant)
        for total in totals
    ]
    mock_processing_service.process_with_details.return_value = (
        MockProcessingService.create_detailed_result(details, row_count=len(details))
    )
    csv_file = create_csv_bytes([
        ['2024-01-01', f'{total:.2f}', merchant, 'deposit', 'EUR']
        for total in totals
    ])
    return client.post(
        '/api/v2/processing-results',
        data={'csv_file': (csv_file, 'test.csv')},
        content_type='multipart/form-data',
        headers=CSRF_HEADERS,
    )


def _stored_transactions(client: Any) -> list[dict[str, Any]]:
    """Fetch all stored transactions of the authenticated user."""
    response = client.get('/api/v2/transactions')
    assert response.status_code == 200
    data: dict[str, Any] = response.get_json()
    return data['transactions']


def _create_correction(
    client: Any,
    original_partner: str,
    **corrected: Any
) -> dict[str, Any]:
    """Create a correction for the authenticated user via the API."""
    payload: dict[str, Any] = {'original_partner': original_partner}
    payload.update(corrected)
    response = client.post(
        '/api/v2/corrections',
        json=payload,
        headers=CSRF_HEADERS,
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


class TestUploadAppliesCorrections:
    """Tests for correction application during transaction upload."""

    def test_upload_applies_correction_case_insensitively(
        self, api_client_with_mock, mock_processing_service
    ):
        """A correction is applied to an upload whose partner differs in case."""
        _create_correction(
            api_client_with_mock,
            'TEST MERCHANT',
            corrected_partner='Test Merchant Ltd',
            corrected_category_id='housing',
        )

        response = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert response.status_code == 201, response.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        assert len(transactions) == 1
        stored = transactions[0]
        assert stored['original_partner'] == 'Test Merchant'
        assert stored['partner'] == 'Test Merchant Ltd'
        assert stored['category_id'] == 'housing'
        # Rules never carry notices; the raw processing notice is kept
        assert stored['notice'] == ''

    def test_upload_without_correction_stores_raw_values(
        self, api_client_with_mock, mock_processing_service
    ):
        """Without a matching correction, raw processing values are stored."""
        response = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Fresh Market'
        )
        assert response.status_code == 201, response.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        assert len(transactions) == 1
        stored = transactions[0]
        assert stored['original_partner'] == 'Fresh Market'
        assert stored['partner'] is None

    def test_partial_correction_falls_back_to_processing_values(
        self, api_client_with_mock, mock_processing_service
    ):
        """Correction fields left empty fall back to the processing values."""
        _create_correction(
            api_client_with_mock,
            'Test Merchant',
            corrected_category_id='housing',
        )

        response = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert response.status_code == 201, response.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        assert len(transactions) == 1
        stored = transactions[0]
        assert stored['original_partner'] == 'Test Merchant'
        assert stored['partner'] is None
        assert stored['category_id'] == 'housing'

    def test_other_users_correction_is_not_applied(
        self, api_client_with_mock, mock_processing_service
    ):
        """Corrections owned by another user do not affect this upload."""
        from flask import current_app
        from whatsthedamage.models.database.correction import Correction

        correction_repo = current_app.extensions['correction_repository']
        correction_repo.create(Correction(
            user_id=999,
            original_partner='Test Merchant',
            corrected_partner='Someone Elses Merchant',
            corrected_category_id='housing',
        ))

        response = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert response.status_code == 201, response.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        assert len(transactions) == 1
        stored = transactions[0]
        assert stored['partner'] is None
        assert stored['category_id'] != 'housing'

    def test_dedup_hash_unchanged_by_corrections(
        self, api_client_with_mock, mock_processing_service
    ):
        """Applying a correction never alters the deduplication key.

        If the hash were computed from corrected values, removing the
        correction and re-uploading would create a duplicate.
        """
        _create_correction(
            api_client_with_mock,
            'Test Merchant',
            corrected_partner='Test Merchant Ltd',
        )

        first = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert first.status_code == 201, first.get_json()

        corrections = api_client_with_mock.get(
            '/api/v2/corrections'
        ).get_json()['corrections']
        delete = api_client_with_mock.delete(
            f"/api/v2/corrections/{corrections[0]['id']}",
            headers=CSRF_HEADERS,
        )
        assert delete.status_code == 200

        second = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert second.status_code == 201, second.get_json()

        assert len(_stored_transactions(api_client_with_mock)) == 1

    def test_reupload_preserves_corrected_transaction(
        self, api_client_with_mock, mock_processing_service
    ):
        """Re-uploading a corrected transaction keeps the correction."""
        first = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert first.status_code == 201, first.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        transaction_id = transactions[0]['id']
        update = api_client_with_mock.put(
            f'/api/v2/transactions/{transaction_id}',
            json={'partner': 'Renamed Merchant'},
            headers=CSRF_HEADERS,
        )
        assert update.status_code == 200, update.get_json()

        second = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant'
        )
        assert second.status_code == 201, second.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        assert len(transactions) == 1
        assert transactions[0]['partner'] == 'Renamed Merchant'

    def test_upload_populates_original_values(
        self, api_client_with_mock, mock_processing_service
    ):
        """Uploads store the raw processing values in the original columns."""
        _create_correction(
            api_client_with_mock,
            'Test Merchant',
            corrected_partner='Test Merchant Ltd',
            corrected_category_id='housing',
        )

        response = _upload(api_client_with_mock, mock_processing_service,
                           merchant='Test Merchant')
        assert response.status_code == 201, response.get_json()

        stored = _stored_transactions(api_client_with_mock)[0]
        assert stored['partner'] == 'Test Merchant Ltd'
        assert stored['category_id'] == 'housing'
        assert stored['original_partner'] == 'Test Merchant'
        # The mock processing result yields no per-row category, so the
        # raw processing category is empty; the corrected one wins
        assert stored['original_category_id'] == ''
        assert stored['original_notice'] == ''

    def test_rule_applies_to_future_upload_while_exception_stays(
        self, api_client_with_mock, mock_processing_service
    ):
        """A later merchant rule does not overwrite an earlier exception."""
        first = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant', amounts=[100.0, 200.0]
        )
        assert first.status_code == 201, first.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        by_amount = {t['amount']: t for t in transactions}

        exception = api_client_with_mock.put(
            f"/api/v2/transactions/{by_amount[100.0]['id']}",
            json={'category_id': 'gifts', 'apply_to_future': False},
            headers=CSRF_HEADERS,
        )
        rule = api_client_with_mock.put(
            f"/api/v2/transactions/{by_amount[200.0]['id']}",
            json={'category_id': 'housing'},
            headers=CSRF_HEADERS,
        )
        assert exception.status_code == 200, exception.get_json()
        assert rule.status_code == 200, rule.get_json()

        third = _upload(
            api_client_with_mock, mock_processing_service,
            merchant='Test Merchant', amount=300.0
        )
        assert third.status_code == 201, third.get_json()

        transactions = _stored_transactions(api_client_with_mock)
        by_amount = {t['amount']: t for t in transactions}
        assert by_amount[100.0]['category_id'] == 'gifts'
        assert by_amount[200.0]['category_id'] == 'housing'
        assert by_amount[300.0]['category_id'] == 'housing'
