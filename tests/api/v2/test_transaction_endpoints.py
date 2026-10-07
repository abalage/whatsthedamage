"""Functional tests for transaction update API endpoints.

Tests for PUT and POST /api/v2/transactions/<id>/undo covering validation,
ownership, persistence, undo semantics, and automatic Correction record
synchronization.
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


class TestApplyToFutureSemantics:
    """Tests for rule vs exception semantics (apply_to_future)."""

    def _list_corrections(self, context: AuthContext) -> list[dict]:
        """Return all corrections of the context user."""
        response = context.client.get('/api/v2/corrections')
        assert response.status_code == 200
        return response.get_json()['corrections']

    def test_exception_mode_category_edit_creates_no_rule(self, auth_context):
        """A category edit with apply_to_future=false updates only the row."""
        transaction = create_transaction(auth_context, apply_to_future=False)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'gifts', 'apply_to_future': False},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['category_id'] == 'gifts'
        assert self._list_corrections(auth_context) == []

    def test_exception_mode_partner_edit_creates_no_rule(self, auth_context):
        """A partner edit with apply_to_future=false updates only the row."""
        transaction = create_transaction(auth_context, apply_to_future=False)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'One-Off Name', 'apply_to_future': False},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['partner'] == 'One-Off Name'
        assert self._list_corrections(auth_context) == []

    def test_notice_edit_never_creates_rule(self, auth_context):
        """Notice corrections are per-transaction and never create rules."""
        transaction = create_transaction(auth_context, apply_to_future=False)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'notice': 'birthday gift'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['notice'] == 'birthday gift'
        assert self._list_corrections(auth_context) == []

    def test_apply_to_future_must_be_boolean(self, auth_context):
        """A non-boolean apply_to_future value is rejected."""
        transaction = create_transaction(auth_context, apply_to_future=False)

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'gifts', 'apply_to_future': 'yes'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_original_values_captured_on_first_correction(self, auth_context):
        """The original category/notice are captured once, not overwritten."""
        transaction = create_transaction(
            auth_context,
            category_id='grocery',
            notice='original notice',
            apply_to_future=False
        )

        first = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'gifts'},
            headers=auth_context.csrf_headers
        ).get_json()
        assert first['category_id'] == 'gifts'
        assert first['original_category_id'] == 'grocery'

        second = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'notice': 'changed notice'},
            headers=auth_context.csrf_headers
        ).get_json()
        assert second['notice'] == 'changed notice'
        assert second['original_notice'] == 'original notice'

        third = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'travel'},
            headers=auth_context.csrf_headers
        ).get_json()
        assert third['category_id'] == 'travel'
        assert third['original_category_id'] == 'grocery'

    def test_exception_stays_when_rule_created_later(self, auth_context):
        """An exception row keeps its values after a later rule edit."""
        first = create_transaction(auth_context, apply_to_future=False)
        second = create_transaction(
            auth_context, date='2026-02-15', apply_to_future=False
        )

        exception = auth_context.client.put(
            f"/api/v2/transactions/{first['id']}",
            json={'category_id': 'gifts', 'apply_to_future': False},
            headers=auth_context.csrf_headers
        )
        rule = auth_context.client.put(
            f"/api/v2/transactions/{second['id']}",
            json={'category_id': 'housing'},
            headers=auth_context.csrf_headers
        )

        assert exception.get_json()['category_id'] == 'gifts'
        assert rule.get_json()['category_id'] == 'housing'

        corrections = self._list_corrections(auth_context)
        assert len(corrections) == 1
        assert corrections[0]['corrected_category_id'] == 'housing'

        stored_first = auth_context.client.get(
            f"/api/v2/transactions/{first['id']}"
        ).get_json()
        assert stored_first['category_id'] == 'gifts'

    def test_create_with_apply_to_future_false_creates_no_rule(
        self, auth_context
    ):
        """A manually created transaction can skip merchant rule creation."""
        create_transaction(
            auth_context, category_id='grocery', apply_to_future=False
        )

        assert self._list_corrections(auth_context) == []


class TestUndoTransaction:
    """Tests for POST /api/v2/transactions/<transaction_id>/undo."""

    def _list_corrections(self, context: AuthContext) -> list[dict]:
        """Return all corrections of the context user."""
        response = context.client.get('/api/v2/corrections')
        assert response.status_code == 200
        return response.get_json()['corrections']

    def _undo(self, context: AuthContext, transaction_id: int):
        """Undo corrections of the given transaction."""
        return context.client.post(
            f'/api/v2/transactions/{transaction_id}/undo',
            headers=context.csrf_headers
        )

    def test_undo_restores_all_corrected_fields(self, auth_context):
        """Undo restores category, partner, and notice to the originals."""
        transaction = create_transaction(
            auth_context,
            category_id='grocery',
            notice='original notice',
            apply_to_future=False
        )

        corrected = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'category_id': 'gifts',
                'partner': 'Test Merchant Ltd',
                'notice': 'changed notice'
            },
            headers=auth_context.csrf_headers
        )
        assert corrected.get_json()['category_id'] == 'gifts'

        response = self._undo(auth_context, transaction['id'])

        assert response.status_code == 200
        data = response.get_json()
        assert data['category_id'] == 'grocery'
        assert data['partner'] is None
        assert data['original_partner'] == 'TEST MERCHANT'
        assert data['notice'] == 'original notice'
        # The originals stay intact so undo remains repeatable
        assert data['original_category_id'] == 'grocery'
        assert data['original_notice'] == 'original notice'

        stored = auth_context.client.get(
            f"/api/v2/transactions/{transaction['id']}"
        ).get_json()
        assert stored['category_id'] == 'grocery'
        assert stored['partner'] is None
        assert stored['notice'] == 'original notice'

    def test_undo_is_a_noop_for_pristine_transaction(self, auth_context):
        """Undoing a transaction without corrections returns it unchanged."""
        transaction = create_transaction(
            auth_context, category_id='grocery', notice='kept notice'
        )

        response = self._undo(auth_context, transaction['id'])

        assert response.status_code == 200
        data = response.get_json()
        assert data['category_id'] == 'grocery'
        assert data['partner'] is None
        assert data['notice'] == 'kept notice'

    def test_undo_is_repeatable_across_correction_cycles(self, auth_context):
        """Undo works after a correct, undo, re-correct sequence."""
        transaction = create_transaction(
            auth_context, category_id='grocery', apply_to_future=False
        )

        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'gifts', 'apply_to_future': False},
            headers=auth_context.csrf_headers
        )
        self._undo(auth_context, transaction['id'])

        recorrected = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'category_id': 'travel', 'apply_to_future': False},
            headers=auth_context.csrf_headers
        )
        assert recorrected.get_json()['category_id'] == 'travel'
        assert recorrected.get_json()['original_category_id'] == 'grocery'

        response = self._undo(auth_context, transaction['id'])

        assert response.status_code == 200
        assert response.get_json()['category_id'] == 'grocery'

    def test_undo_deletes_the_merchant_rule_of_the_transaction(self, auth_context):
        """Undo also removes the merchant rule of the undone transaction."""
        transaction = create_transaction(auth_context)

        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd', 'category_id': 'housing'},
            headers=auth_context.csrf_headers
        )
        assert len(self._list_corrections(auth_context)) == 1

        response = self._undo(auth_context, transaction['id'])
        assert response.status_code == 200

        assert self._list_corrections(auth_context) == []

    def test_undo_keeps_merchant_rules_of_other_merchants(self, auth_context):
        """Undo removes only the rule of the undone transaction's merchant."""
        transaction = create_transaction(auth_context)
        other = create_transaction(
            auth_context, original_partner='OTHER MERCHANT'
        )

        auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'partner': 'Test Merchant Ltd'},
            headers=auth_context.csrf_headers
        )
        auth_context.client.put(
            f"/api/v2/transactions/{other['id']}",
            json={'partner': 'Other Merchant Ltd'},
            headers=auth_context.csrf_headers
        )
        assert len(self._list_corrections(auth_context)) == 2

        response = self._undo(auth_context, transaction['id'])
        assert response.status_code == 200

        corrections = self._list_corrections(auth_context)
        assert len(corrections) == 1
        assert corrections[0]['original_partner'] == 'OTHER MERCHANT'

    def test_undo_unknown_transaction_returns_404(self, auth_context):
        """Undoing a non-existent transaction returns 404."""
        response = self._undo(auth_context, 999999)

        assert response.status_code == 404

    def test_undo_other_users_transaction_returns_403(
        self, auth_context, second_auth_context
    ):
        """Users cannot undo transactions owned by another user."""
        transaction = create_transaction(auth_context)

        response = self._undo(second_auth_context, transaction['id'])

        assert response.status_code == 403

    def test_undo_without_csrf_token_returns_403(self, auth_context):
        """Undo requests missing the CSRF header are rejected."""
        transaction = create_transaction(auth_context)

        response = auth_context.client.post(
            f"/api/v2/transactions/{transaction['id']}/undo"
        )

        assert response.status_code == 403

    def test_undo_without_authentication_returns_401(
        self, api_app, auth_context
    ):
        """Unauthenticated undo requests are rejected."""
        transaction = create_transaction(auth_context)
        client = api_app.test_client()

        response = client.post(
            f"/api/v2/transactions/{transaction['id']}/undo"
        )

        assert response.status_code == 401
