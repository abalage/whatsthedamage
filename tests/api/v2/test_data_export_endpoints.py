"""Functional tests for the data export endpoint (GDPR Art. 15/20).

Covers GET /api/v2/auth/me/export: authentication, completeness of
the exported account, transaction, and correction data, user
scoping, and the exclusion of credential hashes.
"""

from flask import Flask

from tests.api.v2.conftest import AuthContext, create_transaction


def _create_correction(context: AuthContext, **fields: object) -> dict:
    """Create a correction for the context user via the API.

    Args:
        context: Authenticated client context.
        **fields: Corrected values (corrected_partner,
            corrected_category_id).

    Returns:
        The created correction entity as returned by the API.
    """
    payload = {'original_partner': 'TEST MERCHANT'}
    payload.update(fields)
    response = context.client.post(
        '/api/v2/corrections',
        json=payload,
        headers=context.csrf_headers
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


class TestDataExportEndpoint:
    """Tests for GET /api/v2/auth/me/export."""

    def test_requires_authentication(self, api_app: Flask):
        """Without a session cookie the request is rejected."""
        response = api_app.test_client().get('/api/v2/auth/me/export')

        assert response.status_code == 401

    def test_export_contains_all_user_data(
        self, auth_context: AuthContext
    ):
        """Account, transactions, and corrections are exported."""
        create_transaction(auth_context)
        _create_correction(
            auth_context,
            original_partner='OTHER SHOP',
            corrected_partner='Merchant Ltd'
        )

        response = auth_context.client.get('/api/v2/auth/me/export')

        assert response.status_code == 200
        payload = response.get_json()

        assert payload['account']['username'] == 'alice'
        assert payload['account']['opt_in_sharing'] is False

        assert len(payload['transactions']) == 1
        exported_transaction = payload['transactions'][0]
        assert exported_transaction['original_partner'] == (
            'TEST MERCHANT'
        )
        assert exported_transaction['amount'] == -42.5
        assert exported_transaction['account'] == 'main'
        assert exported_transaction['category_id'] == 'grocery'

        # One rule from the transaction create (apply_to_future) and
        # one from the explicit correction create
        assert len(payload['corrections']) == 2
        exported_partners = {
            correction['original_partner']
            for correction in payload['corrections']
        }
        assert exported_partners == {'TEST MERCHANT', 'OTHER SHOP'}
        corrected_partners = {
            correction['corrected_partner']
            for correction in payload['corrections']
        }
        assert 'Merchant Ltd' in corrected_partners

        assert 'attachment' in response.headers.get(
            'Content-Disposition', ''
        )

    def test_export_excludes_credential_hashes(
        self, auth_context: AuthContext
    ):
        """Password and recovery code hashes are never exported."""
        response = auth_context.client.get('/api/v2/auth/me/export')

        assert response.status_code == 200
        payload = response.get_json()
        account = payload['account']

        assert 'password_hash' not in account
        assert 'recovery_code_hash' not in account

    def test_export_is_scoped_to_the_user(
        self, auth_context: AuthContext,
        second_auth_context: AuthContext
    ):
        """Another user's data never appears in the export."""
        create_transaction(second_auth_context)

        response = auth_context.client.get('/api/v2/auth/me/export')

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['account']['username'] == 'alice'
        assert payload['transactions'] == []
        assert payload['corrections'] == []
