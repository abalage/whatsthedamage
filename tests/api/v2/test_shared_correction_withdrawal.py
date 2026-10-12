"""Functional tests for shared correction contribution withdrawal
(GDPR Art. 7(3), Art. 17).

Covers the contribution link recording during opt-in sharing and
the withdrawal performed by the retention purge when the user
requested it with the account deletion.
"""

from datetime import datetime, timedelta, UTC
from typing import Any

from flask import Flask

from whatsthedamage.models.database.shared_correction import (
    SharedCorrection as SharedCorrectionDB
)
from whatsthedamage.models.database.shared_correction_contribution import (
    SharedCorrectionContribution as ContributionDB
)
from tests.api.v2.conftest import AuthContext


PASSWORD = 'password-123456'


def _opt_in(context: AuthContext) -> None:
    """Enable the correction sharing opt-in for the context user.

    Args:
        context: Authenticated client context.
    """
    response = context.client.put(
        '/api/v2/auth/me',
        json={'opt_in_sharing': True},
        headers=context.csrf_headers
    )
    assert response.status_code == 200


def _share_correction(
    context: AuthContext,
    partner: str = 'TEST MERCHANT',
    corrected_partner: str = 'Merchant Ltd'
) -> None:
    """Contribute a correction to the shared corrections.

    Args:
        context: Authenticated client context with opt-in enabled.
        partner: Original partner name to contribute.
        corrected_partner: Corrected partner name (revisions must
            differ between contributors to be counted).
    """
    response = context.client.post(
        '/api/v2/corrections',
        json={
            'original_partner': partner,
            'corrected_partner': corrected_partner,
            'corrected_category_id': 'grocery'
        },
        headers=context.csrf_headers
    )
    assert response.status_code == 201, response.get_json()


def _query_shared_corrections(api_app: Flask) -> list[Any]:
    """Return all shared correction rows.

    Args:
        api_app: Flask application with the test database.

    Returns:
        List of SharedCorrection entities.
    """
    with api_app.app_context():
        session = api_app.extensions['db_session_factory']()
        try:
            return session.query(SharedCorrectionDB).all()
        finally:
            session.close()


def _query_contributions(api_app: Flask) -> list[Any]:
    """Return all contribution link rows.

    Args:
        api_app: Flask application with the test database.

    Returns:
        List of SharedCorrectionContribution entities.
    """
    with api_app.app_context():
        session = api_app.extensions['db_session_factory']()
        try:
            return session.query(ContributionDB).all()
        finally:
            session.close()


def _request_deletion(
    context: AuthContext, revoke_shared_corrections: bool = False
) -> None:
    """Schedule the account deletion with the revocation option.

    Args:
        context: Authenticated client context.
        revoke_shared_corrections: Whether to withdraw the user's
            shared correction contributions.
    """
    response = context.client.delete(
        '/api/v2/auth/account',
        json={
            'password': PASSWORD,
            'revoke_shared_corrections': revoke_shared_corrections
        },
        headers=context.csrf_headers
    )
    assert response.status_code == 200, response.get_json()


def _force_deletion_due(api_app: Flask, user_id: int) -> None:
    """Move the user's scheduled deletion into the past.

    Only the scheduled timestamp is moved so that any revocation
    flag recorded with the deletion request is preserved.

    Args:
        api_app: Flask application with the test database.
        user_id: User identifier.
    """
    with api_app.app_context():
        from whatsthedamage.models.database.user import User as UserDB
        session = api_app.extensions['db_session_factory']()
        try:
            session.query(UserDB).filter(
                UserDB.id == user_id
            ).update({
                'scheduled_deletion_at': (
                    datetime.now(UTC) - timedelta(days=1)
                )
            })
            session.commit()
        finally:
            session.close()


def _run_purge(api_app: Flask) -> dict[str, int]:
    """Run the retention purge job.

    Args:
        api_app: Flask application with the test database.

    Returns:
        Purge result counts.
    """
    with api_app.app_context():
        retention = api_app.extensions['retention_service']
        return retention.purge()


class TestContributionRecording:
    """Tests for the contribution link rows written during sharing."""

    def test_contribution_records_user_link(
        self, api_app: Flask, auth_context: AuthContext
    ):
        """Opting in and sharing records a contribution link row."""
        _opt_in(auth_context)
        _share_correction(auth_context)

        shared = _query_shared_corrections(api_app)
        assert len(shared) == 1

        contributions = _query_contributions(api_app)
        assert len(contributions) == 1
        assert contributions[0].user_id == auth_context.user_id
        assert contributions[0].shared_correction_id == shared[0].id
        assert contributions[0].contribution_count == 1

    def test_no_link_without_opt_in(
        self, api_app: Flask, auth_context: AuthContext
    ):
        """Without opt-in no shared correction or link is written."""
        _share_correction(auth_context)

        assert _query_shared_corrections(api_app) == []
        assert _query_contributions(api_app) == []


class TestWithdrawal:
    """Tests for the withdrawal during the retention purge."""

    def test_withdraw_removes_sole_contributors_data(
        self, api_app: Flask, auth_context: AuthContext
    ):
        """With the flag the shared correction is deleted."""
        _opt_in(auth_context)
        _share_correction(auth_context)
        _request_deletion(auth_context, revoke_shared_corrections=True)
        _force_deletion_due(api_app, auth_context.user_id)

        result = _run_purge(api_app)

        assert result['accounts_deleted'] == 1
        assert _query_shared_corrections(api_app) == []
        assert _query_contributions(api_app) == []

    def test_without_flag_contributions_are_retained(
        self, api_app: Flask, auth_context: AuthContext
    ):
        """Without the flag the shared correction survives the purge."""
        _opt_in(auth_context)
        _share_correction(auth_context)
        _request_deletion(auth_context, revoke_shared_corrections=False)
        _force_deletion_due(api_app, auth_context.user_id)

        result = _run_purge(api_app)

        assert result['accounts_deleted'] == 1
        assert len(_query_shared_corrections(api_app)) == 1
        # The link rows of the deleted user are removed by the user
        # cascade; the shared correction itself is retained.
        assert _query_contributions(api_app) == []

    def test_withdraw_decrements_multi_contributor_count(
        self, api_app: Flask, auth_context: AuthContext,
        second_auth_context: AuthContext
    ):
        """A withdrawn contributor decrements but keeps shared rows.

        Two users contribute revisions to the same partner; the first
        user's withdrawal decrements the contribution count and keeps
        the row (the second user's revisions remain).
        """
        _opt_in(auth_context)
        _share_correction(auth_context, 'TEST MERCHANT')
        _opt_in(second_auth_context)
        _share_correction(
            second_auth_context, 'TEST MERCHANT', 'Merchant Ltd 2'
        )

        shared = _query_shared_corrections(api_app)
        assert len(shared) == 1
        assert shared[0].contribution_count == 2

        _request_deletion(auth_context, revoke_shared_corrections=True)
        _force_deletion_due(api_app, auth_context.user_id)
        _run_purge(api_app)

        shared = _query_shared_corrections(api_app)
        assert len(shared) == 1
        assert shared[0].contribution_count == 1

    def test_withdraw_deletes_row_when_last_contributor_leaves(
        self, api_app: Flask, auth_context: AuthContext,
        second_auth_context: AuthContext
    ):
        """The row is deleted once every contributor has withdrawn."""
        _opt_in(auth_context)
        _share_correction(auth_context, 'TEST MERCHANT')
        _opt_in(second_auth_context)
        _share_correction(
            second_auth_context, 'TEST MERCHANT', 'Merchant Ltd 2'
        )

        _request_deletion(auth_context, revoke_shared_corrections=True)
        _force_deletion_due(api_app, auth_context.user_id)
        _run_purge(api_app)
        assert len(_query_shared_corrections(api_app)) == 1

        _request_deletion(
            second_auth_context, revoke_shared_corrections=True
        )
        _force_deletion_due(api_app, second_auth_context.user_id)
        _run_purge(api_app)

        assert _query_shared_corrections(api_app) == []
        assert _query_contributions(api_app) == []

    def test_login_cancel_restores_nothing_and_keeps_contributions(
        self, api_app: Flask, auth_context: AuthContext
    ):
        """Canceling the deletion keeps the contributions intact."""
        _opt_in(auth_context)
        _share_correction(auth_context)
        _request_deletion(auth_context, revoke_shared_corrections=True)

        login = auth_context.client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login.status_code == 200

        _run_purge(api_app)

        # Nothing was withdrawn: the account and the shared
        # correction are still there
        assert len(_query_shared_corrections(api_app)) == 1
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            assert user_repo.find_by_username('alice') is not None
