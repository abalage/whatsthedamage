"""Functional tests for transaction update API endpoints.

Tests for PUT /api/v2/transactions/<id> covering validation, ownership,
persistence, and automatic Correction record synchronization.
"""

from tests.api.v2.conftest import AuthContext, create_transaction


class TestUpdateTransaction:
    """Tests for PUT /api/v2/transactions/<transaction_id>."""

    def test_update_partner_returns_updated_transaction(self, auth_context):
        """Updating partner returns the corrected transaction."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['partner'] == 'Test Merchant Ltd'
        assert data['original_partner'] == transaction['original_partner']

    def test_update_category_id_persists(self, auth_context):
        """Updating category_id is persisted and returned."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'housing'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['category_id'] == 'housing'

        stored = auth_context.client.get(
            f"/api/v2/transactions/{transaction['id']}"
        )
        assert stored.get_json()['category_id'] == 'housing'

    def test_update_notice_persists(self, auth_context):
        """Updating notice is persisted and returned."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'notice': 'birthday gift'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['notice'] == 'birthday gift'

        stored = auth_context.client.get(
            f"/api/v2/transactions/{transaction['id']}"
        )
        assert stored.get_json()['notice'] == 'birthday gift'

    def test_update_all_fields_together(self, auth_context):
        """All three correctable fields can be updated in one request."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'partner': 'Test Merchant Ltd',
                'category_id': 'housing',
                'notice': 'rent share'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['partner'] == 'Test Merchant Ltd'
        assert data['category_id'] == 'housing'
        assert data['notice'] == 'rent share'

    def test_update_without_authentication_returns_401(
        self, api_app, auth_context
    ):
        """Unauthenticated update requests are rejected."""
        transaction = create_transaction(auth_context)
        client = api_app.test_client()

        response = client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Nope'}
        )

        assert response.status_code == 401

    def test_update_without_csrf_token_returns_403(self, auth_context):
        """Update requests missing the CSRF header are rejected."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Nope'}
        )

        assert response.status_code == 403

    def test_update_unknown_transaction_returns_404(self, auth_context):
        """Updating a non-existent transaction returns 404."""
        response = auth_context.client.put(
            '/api/v2/transactions/999999',
            json={'partner': 'Nope'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 404

    def test_update_other_users_transaction_returns_403(
        self, auth_context, second_auth_context
    ):
        """Users cannot update transactions owned by another user."""
        transaction = create_transaction(auth_context)

        response = second_auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Nope'},
            headers=second_auth_context.csrf_headers
        )

        assert response.status_code == 403

    def test_update_with_empty_body_returns_400(self, auth_context):
        """An empty JSON body is rejected."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_update_with_only_unknown_fields_returns_400(self, auth_context):
        """A body without any correctable field is rejected."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'amount': 100},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400


class TestUpdateTransactionCorrectionSync:
    """Tests for automatic Correction synchronization on transaction edit."""

    def _list_corrections(self, context: AuthContext) -> list[dict]:
        """Return all corrections of the context user."""
        response = context.client.get('/api/v2/corrections')
        assert response.status_code == 200
        return response.get_json()['corrections']

    def test_update_creates_correction_for_original_partner(self, auth_context):
        """Editing a transaction creates a correction keyed by
        original_partner.
        """
        transaction = create_transaction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd'},
            headers=auth_context.csrf_headers
        )
        assert response.status_code == 200

        corrections = self._list_corrections(auth_context)
        assert len(corrections) == 1
        assert corrections[0]['original_partner'] == 'TEST MERCHANT'
        assert corrections[0]['corrected_partner'] == 'Test Merchant Ltd'

    def test_repeated_updates_modify_single_correction(self, auth_context):
        """Editing the same merchant twice updates the existing correction
        instead of creating a duplicate.
        """
        transaction = create_transaction(auth_context)

        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd'},
            headers=auth_context.csrf_headers
        )
        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant GmbH'},
            headers=auth_context.csrf_headers
        )

        corrections = self._list_corrections(auth_context)
        assert len(corrections) == 1
        assert corrections[0]['corrected_partner'] == 'Test Merchant GmbH'

    def test_correction_is_scoped_to_owning_user(
        self, auth_context, second_auth_context
    ):
        """Corrections created by one user are not visible to another."""
        transaction = create_transaction(auth_context)

        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd'},
            headers=auth_context.csrf_headers
        )

        assert len(self._list_corrections(auth_context)) == 1
        assert self._list_corrections(second_auth_context) == []
