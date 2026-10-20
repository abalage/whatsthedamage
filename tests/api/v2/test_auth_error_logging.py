"""Functional tests for server-side exception logging in auth endpoints.

Unexpected exceptions must never leak to the client (generic 500 with
INTERNAL_ERROR code) but must be logged server-side with the full
traceback so failures like the one behind the "Login failed" 500s can
be diagnosed.
"""

import logging

import pytest
from flask import Flask

from tests.api.v2.conftest import AuthContext


PASSWORD = 'password-123456'

ENDPOINTS_LOGGER = 'whatsthedamage.api.v2.auth.endpoints'


class _ErrorRecorder(logging.Handler):
    """Logging handler that records ERROR records for inspection."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class TestLoginErrorLogging:
    """Tests for the logging of unexpected login failures."""

    def test_unexpected_exception_is_logged_not_leaked(
        self,
        api_app: Flask,
        auth_context: AuthContext,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A login failure returns a generic 500 and logs the exception.

        The client response must not contain the exception text; the
        full traceback is logged server-side instead.
        """

        def boom(**kwargs: object) -> None:
            raise RuntimeError("boom: session insert failed")

        service = api_app.extensions['account_service']
        monkeypatch.setattr(service, 'login_user', boom)

        logger = logging.getLogger(ENDPOINTS_LOGGER)
        recorder = _ErrorRecorder()
        logger.addHandler(recorder)
        try:
            response = auth_context.client.post(
                '/api/v2/auth/login',
                json={
                    'username': auth_context.username,
                    'password': PASSWORD
                }
            )
        finally:
            logger.removeHandler(recorder)

        assert response.status_code == 500
        body = response.get_json()
        assert body['code'] == 'INTERNAL_ERROR'
        assert body['error'] == 'Login failed'
        assert 'boom' not in str(body)

        assert recorder.records, (
            'expected an ERROR log record for the failed login'
        )
        record = recorder.records[-1]
        traceback_text = format_exception_text(record)
        assert 'RuntimeError' in traceback_text
        assert 'boom: session insert failed' in traceback_text


def format_exception_text(record: logging.LogRecord) -> str:
    """Format a record's exception info for assertion purposes.

    Args:
        record: Log record with exc_info set.

    Returns:
        Formatted traceback string.
    """
    import traceback
    assert record.exc_info is not None
    return ''.join(traceback.format_exception(*record.exc_info))
