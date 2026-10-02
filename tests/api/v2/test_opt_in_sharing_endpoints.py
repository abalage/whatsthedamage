"""Functional tests for the correction sharing opt-in flow.

Covers PUT /api/v2/auth/me (US-6 opt-in and US-8 revoke) and the
sharing hook on merchant-rule correction writes.
"""

import hashlib
from typing import Any, Optional

from tests.api.v2.conftest import AuthContext, create_transaction


def _partner_hash(partner: str) -> str:
    """Compute the anonymized partner hash used by shared corrections.

    Args:
        partner: Original partner name.

    Returns:
        SHA-256 hex digest of the lowercase partner name.
    """
    return hashlib.sha256(partner.lower().encode('utf-8')).hexdigest()


def _find_shared(api_app: Any, partner: str) -> Optional[Any]:
    """Look up the shared correction contributed for a partner.

    Args:
        api_app: Flask application holding the repositories.
        partner: Original partner name.

    Returns:
        The SharedCorrection entity or None.
    """
    repo = api_app.extensions['shared_correction_repository']
    return repo.find_by_original_partner_hash(_partner_hash(partner))


def _set_opt_in(context: AuthContext, opt_in: bool) -> None:
    """Update the sharing preference via the API.

    Args:
        context: Authenticated client context.
        opt_in: New opt-in value.
    """
    response = context.client.put(
        '/api/v2/auth/me',
        json={'opt_in_sharing': opt_in},
        headers=context.csrf_headers
    )
    assert response.status_code == 200, response.get_json()


def _create_correction(
    context: AuthContext,
    original_partner: str,
    **fields: Any
) -> Any:
    """Create a merchant-rule correction via the API.

    Args:
        context: Authenticated client context.
        original_partner: Original partner name to correct.
        **fields: Corrected values (corrected_partner,
            corrected_category_id).

    Returns:
        The created correction entity as returned by the API.
    """
    payload: dict[str, Any] = {'original_partner': original_partner}
    payload.update(fields)
    response = context.client.post(
        '/api/v2/corrections',
        json=payload,
        headers=context.csrf_headers
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


class TestUpdateMe:
    """Tests for PUT /api/v2/auth/me."""

    def test_update_opt_in_returns_updated_user(self, auth_context):
        """Opting in returns the user with the new preference."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': True},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['id'] == auth_context.user_id
        assert data['user']['username'] == auth_context.username
        assert data['user']['opt_in_sharing'] is True

    def test_update_opt_in_is_persisted(self, auth_context):
        """The new preference is reflected by GET /auth/me."""
        _set_opt_in(auth_context, True)

        response = auth_context.client.get('/api/v2/auth/me')

        assert response.status_code == 200
        assert response.get_json()['user']['opt_in_sharing'] is True

    def test_default_opt_in_is_false(self, auth_context):
        """Newly registered users are opted out by default."""
        response = auth_context.client.get('/api/v2/auth/me')

        assert response.status_code == 200
        assert response.get_json()['user']['opt_in_sharing'] is False

    def test_revoke_opt_in(self, auth_context):
        """Revoking the opt-in persists False."""
        _set_opt_in(auth_context, True)
        _set_opt_in(auth_context, False)

        response = auth_context.client.get('/api/v2/auth/me')

        assert response.get_json()['user']['opt_in_sharing'] is False

    def test_missing_opt_in_returns_400(self, auth_context):
        """Missing opt_in_sharing field is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_non_boolean_opt_in_returns_400(self, auth_context):
        """Non-boolean opt_in_sharing value is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': 'yes'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_without_authentication_returns_401(self, api_app):
        """Unauthenticated requests are rejected."""
        response = api_app.test_client().put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': True}
        )

        assert response.status_code == 401

    def test_without_csrf_returns_403(self, auth_context):
        """Requests without a CSRF token are rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': True}
        )

        assert response.status_code == 403


class TestCorrectionSharing:
    """Tests for the sharing hook on merchant-rule writes."""

    def test_opt_out_default_shares_nothing(self, api_app, auth_context):
        """Corrections are not shared while the user is opted out."""
        _create_correction(
            auth_context,
            'OPT OUT SHOP',
            corrected_partner='Opt Out Shop Ltd',
            corrected_category_id='housing'
        )

        assert _find_shared(api_app, 'OPT OUT SHOP') is None

    def test_opt_in_shares_correction_on_create(
        self, api_app, auth_context
    ):
        """Opting in contributes the merchant rule on creation."""
        _set_opt_in(auth_context, True)
        _create_correction(
            auth_context,
            'TEST MERCHANT',
            corrected_partner='Test Merchant Ltd',
            corrected_category_id='housing'
        )

        shared = _find_shared(api_app, 'TEST MERCHANT')
        assert shared is not None
        assert shared.original_partner_hash == _partner_hash(
            'TEST MERCHANT'
        )
        assert shared.corrected_partner == 'Test Merchant Ltd'
        assert shared.corrected_category_id == 'housing'
        assert shared.corrected_notice is None
        assert shared.contribution_count == 1

    def test_revoke_stops_future_sharing(self, api_app, auth_context):
        """US-8: revoking stops future contributions, old ones remain."""
        _set_opt_in(auth_context, True)
        _create_correction(
            auth_context,
            'KEPT SHOP',
            corrected_category_id='grocery'
        )
        _set_opt_in(auth_context, False)
        _create_correction(
            auth_context,
            'NEW SHOP',
            corrected_category_id='housing'
        )

        assert _find_shared(api_app, 'KEPT SHOP') is not None
        assert _find_shared(api_app, 'NEW SHOP') is None

    def test_correction_without_category_is_not_shared(
        self, api_app, auth_context
    ):
        """Merchant-name-only rules are not shared (category required)."""
        _set_opt_in(auth_context, True)
        _create_correction(
            auth_context,
            'NAME ONLY SHOP',
            corrected_partner='Name Only Shop Ltd'
        )

        assert _find_shared(api_app, 'NAME ONLY SHOP') is None

    def test_rule_mode_transaction_update_shares(
        self, api_app, auth_context
    ):
        """Rule-mode transaction corrections contribute on opt-in."""
        _set_opt_in(auth_context, True)
        transaction = create_transaction(auth_context, category_id='')

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'category_id': 'housing',
                'apply_to_future': True
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        shared = _find_shared(api_app, 'TEST MERCHANT')
        assert shared is not None
        assert shared.corrected_category_id == 'housing'
        assert shared.contribution_count == 1

    def test_exception_mode_transaction_update_does_not_share(
        self, api_app, auth_context
    ):
        """Exception-mode corrections are never shared."""
        _set_opt_in(auth_context, True)
        transaction = create_transaction(auth_context, category_id='')

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'category_id': 'housing',
                'apply_to_future': False
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        assert _find_shared(api_app, 'TEST MERCHANT') is None

    def test_notice_only_transaction_update_does_not_share(
        self, api_app, auth_context
    ):
        """Notice corrections never create rules and are never shared."""
        _set_opt_in(auth_context, True)
        transaction = create_transaction(auth_context, category_id='')

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={'notice': 'my note'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        assert _find_shared(api_app, 'TEST MERCHANT') is None

    def test_rule_mode_transaction_create_shares(
        self, api_app, auth_context
    ):
        """Creating a transaction with a rule-mode category contributes."""
        _set_opt_in(auth_context, True)

        create_transaction(auth_context, category_id='housing')

        shared = _find_shared(api_app, 'TEST MERCHANT')
        assert shared is not None
        assert shared.corrected_category_id == 'housing'
        assert shared.contribution_count == 1

    def test_rule_update_reshares_latest_values(
        self, api_app, auth_context
    ):
        """Updating a rule re-contributes the latest values."""
        _set_opt_in(auth_context, True)
        correction = _create_correction(
            auth_context,
            'UPDATED SHOP',
            corrected_category_id='grocery'
        )

        response = auth_context.client.put(
            f"/api/v2/corrections/{correction['id']}",
            json={'corrected_category_id': 'housing'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        shared = _find_shared(api_app, 'UPDATED SHOP')
        assert shared is not None
        assert shared.corrected_category_id == 'housing'
        assert shared.contribution_count == 2

    def test_rule_update_with_same_values_does_not_recount(
        self, api_app, auth_context
    ):
        """Re-contributing identical values does not increment the count."""
        _set_opt_in(auth_context, True)
        correction = _create_correction(
            auth_context,
            'UNCHANGED SHOP',
            corrected_category_id='housing'
        )

        response = auth_context.client.put(
            f"/api/v2/corrections/{correction['id']}",
            json={'corrected_category_id': 'housing'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        shared = _find_shared(api_app, 'UNCHANGED SHOP')
        assert shared is not None
        assert shared.contribution_count == 1

    def test_partner_only_transaction_edit_shares_rule_category(
        self, api_app, auth_context
    ):
        """Partner-only edits share the rule's stored category."""
        _set_opt_in(auth_context, True)
        _create_correction(
            auth_context,
            'TEST MERCHANT',
            corrected_category_id='grocery'
        )
        transaction = create_transaction(auth_context, category_id='')

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'partner': 'Test Merchant Ltd',
                'apply_to_future': True
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        shared = _find_shared(api_app, 'TEST MERCHANT')
        assert shared is not None
        assert shared.corrected_partner == 'Test Merchant Ltd'
        assert shared.corrected_category_id == 'grocery'

    def test_clearing_rule_category_stops_sharing(
        self, api_app, auth_context
    ):
        """A rule without a category is not shared; prior values remain."""
        _set_opt_in(auth_context, True)
        _create_correction(
            auth_context,
            'CLEARED SHOP',
            corrected_category_id='housing'
        )
        transaction = create_transaction(
            auth_context,
            original_partner='CLEARED SHOP',
            category_id=''
        )

        response = auth_context.client.put(
            f"/api/v2/transactions/{transaction['id']}",
            json={
                'category_id': None,
                'apply_to_future': True
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200, response.get_json()
        shared = _find_shared(api_app, 'CLEARED SHOP')
        assert shared is not None
        assert shared.corrected_category_id == 'housing'
        assert shared.contribution_count == 1

    def test_non_string_category_is_not_shared(
        self, api_app, auth_context
    ):
        """Invalid category values are stored as rules but never shared."""
        _set_opt_in(auth_context, True)

        _create_correction(
            auth_context,
            'INT CATEGORY SHOP',
            corrected_category_id=12345
        )

        assert _find_shared(api_app, 'INT CATEGORY SHOP') is None
