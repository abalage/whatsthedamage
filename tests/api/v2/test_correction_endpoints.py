"""Functional tests for correction API endpoints.

Tests for the /api/v2/corrections CRUD endpoints covering validation,
ownership, pagination, and authentication.
"""

from tests.api.v2.conftest import AuthContext


def create_correction(
    context: AuthContext,
    original_partner: str = 'TEST MERCHANT',
    **fields: object
) -> dict:
    """Create a correction for the context user via the API.

    Args:
        context: Authenticated client context.
        original_partner: Original partner name to correct.
        **fields: Corrected values (corrected_partner,
            corrected_category_id).

    Returns:
        The created correction entity as returned by the API.
    """
    payload = {'original_partner': original_partner}
    payload.update(fields)
    response = context.client.post(
        '/api/v2/corrections',
        json=payload,
        headers=context.csrf_headers
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


class TestListCorrections:
    """Tests for GET /api/v2/corrections."""

    def test_list_returns_user_corrections(self, auth_context):
        """Corrections created by the user are listed."""
        create_correction(auth_context, corrected_partner='Merchant Ltd')
        create_correction(
            auth_context,
            original_partner='OTHER SHOP',
            corrected_category_id='housing'
        )

        response = auth_context.client.get('/api/v2/corrections')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total_count'] == 2
        assert len(data['corrections']) == 2

    def test_list_applies_pagination(self, auth_context):
        """limit and offset query parameters are applied."""
        create_correction(auth_context, original_partner='SHOP A')
        create_correction(auth_context, original_partner='SHOP B')

        response = auth_context.client.get(
            '/api/v2/corrections?limit=1&offset=1'
        )

        data = response.get_json()
        assert data['total_count'] == 2
        assert len(data['corrections']) == 1
        assert data['corrections'][0]['original_partner'] == 'SHOP B'

    def test_list_filters_by_original_partner(self, auth_context):
        """original_partner query parameter filters the list."""
        create_correction(auth_context, original_partner='SHOP A')
        create_correction(auth_context, original_partner='SHOP B')

        response = auth_context.client.get(
            '/api/v2/corrections?original_partner=SHOP A'
        )

        data = response.get_json()
        assert data['total_count'] == 1
        assert data['corrections'][0]['original_partner'] == 'SHOP A'

    def test_list_is_scoped_to_owning_user(
        self, auth_context, second_auth_context
    ):
        """One user's corrections are not listed for another user."""
        create_correction(auth_context, corrected_partner='Merchant Ltd')

        response = second_auth_context.client.get('/api/v2/corrections')

        assert response.get_json()['corrections'] == []

    def test_list_without_authentication_returns_401(self, api_app):
        """Unauthenticated list requests are rejected."""
        response = api_app.test_client().get('/api/v2/corrections')

        assert response.status_code == 401


class TestCreateCorrection:
    """Tests for POST /api/v2/corrections."""

    def test_create_returns_201_with_entity(self, auth_context):
        """Creating a correction returns the stored entity."""
        response = auth_context.client.post(
            '/api/v2/corrections',
            json={
                'original_partner': 'TEST MERCHANT',
                'corrected_partner': 'Test Merchant Ltd',
                'corrected_category_id': 'housing'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['original_partner'] == 'TEST MERCHANT'
        assert data['corrected_partner'] == 'Test Merchant Ltd'
        assert data['corrected_category_id'] == 'housing'

    def test_create_without_original_partner_returns_400(
        self, auth_context
    ):
        """Missing original_partner is rejected."""
        response = auth_context.client.post(
            '/api/v2/corrections',
            json={'corrected_partner': 'Nope'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_create_duplicate_returns_409(self, auth_context):
        """Creating a second correction for the same partner fails."""
        create_correction(auth_context, corrected_partner='Merchant Ltd')

        response = auth_context.client.post(
            '/api/v2/corrections',
            json={
                'original_partner': 'TEST MERCHANT',
                'corrected_partner': 'Other'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 409
        assert response.get_json()['code'] == 'DUPLICATE_CORRECTION'

    def test_create_without_authentication_returns_401(self, api_app):
        """Unauthenticated create requests are rejected."""
        response = api_app.test_client().post(
            '/api/v2/corrections',
            json={'original_partner': 'TEST MERCHANT'}
        )

        assert response.status_code == 401

    def test_create_without_csrf_token_returns_403(self, auth_context):
        """Create requests missing the CSRF header are rejected."""
        response = auth_context.client.post(
            '/api/v2/corrections',
            json={'original_partner': 'TEST MERCHANT'}
        )

        assert response.status_code == 403


class TestGetCorrection:
    """Tests for GET /api/v2/corrections/<correction_id>."""

    def test_get_returns_correction(self, auth_context):
        """A correction can be fetched by its identifier."""
        correction = create_correction(auth_context)

        response = auth_context.client.get(
            f"/api/v2/corrections/{correction['id']}"
        )

        assert response.status_code == 200
        assert response.get_json()['id'] == correction['id']

    def test_get_unknown_returns_404(self, auth_context):
        """Fetching a non-existent correction returns 404."""
        response = auth_context.client.get('/api/v2/corrections/999999')

        assert response.status_code == 404

    def test_get_other_users_correction_returns_403(
        self, auth_context, second_auth_context
    ):
        """Users cannot fetch corrections owned by another user."""
        correction = create_correction(auth_context)

        response = second_auth_context.client.get(
            f"/api/v2/corrections/{correction['id']}"
        )

        assert response.status_code == 403


class TestUpdateCorrection:
    """Tests for PUT /api/v2/corrections/<correction_id>."""

    def test_update_returns_updated_correction(self, auth_context):
        """Corrected values can be updated."""
        correction = create_correction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/corrections/{correction['id']}",
            json={'corrected_partner': 'Renamed Ltd'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['corrected_partner'] == 'Renamed Ltd'

    def test_update_without_fields_returns_400(self, auth_context):
        """An update without correctable fields is rejected."""
        correction = create_correction(auth_context)

        response = auth_context.client.put(
            f"/api/v2/corrections/{correction['id']}",
            json={},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_update_unknown_returns_404(self, auth_context):
        """Updating a non-existent correction returns 404."""
        response = auth_context.client.put(
            '/api/v2/corrections/999999',
            json={'corrected_partner': 'Nope'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 404

    def test_update_other_users_correction_returns_403(
        self, auth_context, second_auth_context
    ):
        """Users cannot update corrections owned by another user."""
        correction = create_correction(auth_context)

        response = second_auth_context.client.put(
            f"/api/v2/corrections/{correction['id']}",
            json={'corrected_partner': 'Nope'},
            headers=second_auth_context.csrf_headers
        )

        assert response.status_code == 403


class TestDeleteCorrection:
    """Tests for DELETE /api/v2/corrections/<correction_id>."""

    def test_delete_removes_correction(self, auth_context):
        """A correction can be deleted by its owner."""
        correction = create_correction(auth_context)

        response = auth_context.client.delete(
            f"/api/v2/corrections/{correction['id']}",
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        stored = auth_context.client.get(
            f"/api/v2/corrections/{correction['id']}"
        )
        assert stored.status_code == 404

    def test_delete_unknown_returns_404(self, auth_context):
        """Deleting a non-existent correction returns 404."""
        response = auth_context.client.delete(
            '/api/v2/corrections/999999',
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 404

    def test_delete_other_users_correction_returns_403(
        self, auth_context, second_auth_context
    ):
        """Users cannot delete corrections owned by another user."""
        correction = create_correction(auth_context)

        response = second_auth_context.client.delete(
            f"/api/v2/corrections/{correction['id']}",
            headers=second_auth_context.csrf_headers
        )

        assert response.status_code == 403

    def test_delete_without_csrf_token_returns_403(self, auth_context):
        """Delete requests missing the CSRF header are rejected."""
        correction = create_correction(auth_context)

        response = auth_context.client.delete(
            f"/api/v2/corrections/{correction['id']}"
        )

        assert response.status_code == 403
