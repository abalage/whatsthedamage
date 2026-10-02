"""Regression tests for API test fixture database isolation.

Guards against test fixtures silently writing processing results and
transactions into the developer's default app.db database (see the
temporary database override in tests/api_fixtures.py).
"""

import pytest


class TestApiFixtureDatabaseIsolation:
    """Ensure API test clients never connect to the default database."""

    @pytest.mark.parametrize('fixture_name', ['api_client', 'api_client_with_mock'])
    def test_client_uses_isolated_database(self, request, fixture_name):
        """Assert the test client's engine does not point at app.db.

        Test Cases:
            The Flask app behind the API test fixtures must be backed by
            a throwaway SQLite database, never the default app.db used by
            development instances.
        """
        client = request.getfixturevalue(fixture_name)
        engine = client.application.extensions['db_engine']
        database_url = str(engine.url)
        assert 'app.db' not in database_url
        assert database_url.startswith('sqlite:///')

    def test_environment_variable_is_restored(self):
        """Assert WHATSTHEDAMAGE_DATABASE_URI is restored after teardown.

        Test Cases:
            The fixture overrides WHATSTHEDAMAGE_DATABASE_URI while the test
            client is active and must restore the previous value afterwards.
        """
        import os
        from tests.api_fixtures import _create_test_client

        previous_uri = 'sqlite:///custom-test.db'
        os.environ['WHATSTHEDAMAGE_DATABASE_URI'] = previous_uri
        try:
            with _create_test_client():
                assert os.environ['WHATSTHEDAMAGE_DATABASE_URI'] != previous_uri
            assert os.environ['WHATSTHEDAMAGE_DATABASE_URI'] == previous_uri
        finally:
            os.environ.pop('WHATSTHEDAMAGE_DATABASE_URI', None)
