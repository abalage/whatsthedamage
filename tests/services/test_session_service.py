"""Tests for SessionService."""

import pytest
from flask import Flask, session

from whatsthedamage.services.session_service import (
    SessionService,
    FormData,
    TableData,
)


@pytest.fixture
def app():
    """Create Flask app for testing with session support."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    return app


@pytest.fixture
def session_service():
    """Create SessionService instance."""
    return SessionService()


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        'filename': 'test.csv',
        'config': 'config.yml',
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'verbose': True,
        'no_currency_format': True,
        'filter': 'January',
        'ml': True
    }


@pytest.fixture
def sample_table_data():
    """Sample table data for testing."""
    return {
        'headers': ['Category', 'Amount'],
        'rows': [
            [
                {'data': 'Food', 'sort': 'food'},
                {'data': '100.00', 'sort': 100.0}
            ]
        ]
    }


class TestFormData:
    """Tests for FormData dataclass."""

    def test_form_data_default_values(self):
        """Test FormData with default values."""
        form_data = FormData()
        assert form_data.filename is None
        assert form_data.verbose is False
        assert form_data.ml is False

    @pytest.mark.parametrize("input_data,expected_values", [
        # Full data
        (
            {
                'filename': 'test.csv', 'config': 'config.yml',
                'start_date': '2023-01-01', 'end_date': '2023-12-31',
                'verbose': True, 'no_currency_format': True,
                'filter': 'January', 'ml': True
            },
            {
                'filename': 'test.csv', 'config': 'config.yml',
                'start_date': '2023-01-01', 'end_date': '2023-12-31',
                'verbose': True, 'no_currency_format': True,
                'filter': 'January', 'ml': True
            }
        ),
        # Partial data
        (
            {'filename': 'test.csv', 'start_date': '2023-01-01'},
            {'filename': 'test.csv', 'start_date': '2023-01-01', 'config': None, 'verbose': False}
        ),
        # Boolean conversion
        (
            {'verbose': 'true', 'no_currency_format': '', 'ml': 1},
            {'verbose': True, 'no_currency_format': False, 'ml': True}
        ),
    ])
    def test_form_data_from_dict(self, input_data, expected_values):
        """Test FormData.from_dict with various inputs."""
        form_data = FormData.from_dict(input_data)
        for key, value in expected_values.items():
            assert getattr(form_data, key) == value

    def test_form_data_roundtrip(self, sample_form_data):
        """Test FormData roundtrip through dict."""
        original = FormData.from_dict(sample_form_data)
        data = original.to_dict()
        restored = FormData.from_dict(data)

        assert restored.filename == original.filename
        assert restored.verbose == original.verbose
        assert restored.ml == original.ml


class TestTableData:
    """Tests for TableData dataclass."""

    @pytest.mark.parametrize("input_data,expected", [
        # Default/empty
        ({}, {'headers': [], 'rows': []}),
        # With data
        (
            {
                'headers': ['Category', 'Amount'],
                'rows': [[{'data': 'Food', 'sort': 'food'}, {'data': '100.00', 'sort': 100.0}]]
            },
            {'headers': ['Category', 'Amount'], 'row_count': 1, 'first_cell': 'Food'}
        ),
    ])
    def test_table_data_from_dict(self, input_data, expected):
        """Test TableData.from_dict with various inputs."""
        table_data = TableData.from_dict(input_data)
        assert table_data.headers == expected['headers']
        if 'row_count' in expected:
            assert len(table_data.rows) == expected['row_count']
            assert table_data.rows[0][0]['data'] == expected['first_cell']
        else:
            assert table_data.rows == expected['rows']

    def test_table_data_roundtrip(self, sample_table_data):
        """Test TableData roundtrip through dict."""
        original = TableData.from_dict(sample_table_data)
        data = original.to_dict()
        restored = TableData.from_dict(data)

        assert restored.headers == original.headers
        assert len(restored.rows) == len(original.rows)


class TestSessionServiceFormData:
    """Tests for SessionService form data management."""

    def test_store_and_retrieve_form_data(self, app, session_service, sample_form_data):
        """Test storing and retrieving form data."""
        with app.test_request_context():
            # Store
            session_service.store_form_data(sample_form_data)
            assert session['form_data'] == sample_form_data

            # Retrieve
            retrieved = session_service.retrieve_form_data()
            assert retrieved is not None
            assert retrieved.filename == 'test.csv'
            assert retrieved.verbose is True

    def test_retrieve_form_data_when_missing(self, app, session_service):
        """Test retrieving form data when none exists."""
        with app.test_request_context():
            assert session_service.retrieve_form_data() is None
            assert not session_service.has_form_data()

    def test_clear_form_data(self, app, session_service, sample_form_data):
        """Test clearing form data from session."""
        with app.test_request_context():
            session_service.store_form_data(sample_form_data)
            assert session_service.has_form_data()

            session_service.clear_form_data()
            assert not session_service.has_form_data()


class TestSessionServiceResult:
    """Tests for SessionService result management."""

    def test_store_and_retrieve_result(self, app, session_service, sample_table_data):
        """Test storing and retrieving result."""
        with app.test_request_context():
            html_result = '<table><tr><td>Test</td></tr></table>'

            # Store
            session_service.store_result(html_result, sample_table_data)
            assert session['result'] == html_result
            assert session['table_data'] == sample_table_data

            # Retrieve
            result = session_service.retrieve_result()
            assert result is not None
            retrieved_html, retrieved_table = result
            assert retrieved_html == html_result
            assert retrieved_table.headers == ['Category', 'Amount']

    @pytest.mark.parametrize("has_html,has_table,expected_exists", [
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (True, True, True),
    ])
    def test_has_result_conditions(self, app, session_service, has_html, has_table, expected_exists):
        """Test checking if result exists under various conditions."""
        with app.test_request_context():
            if has_html:
                session['result'] = '<table></table>'
            if has_table:
                session['table_data'] = {'headers': [], 'rows': []}

            assert session_service.has_result() == expected_exists

    def test_retrieve_result_when_missing(self, app, session_service):
        """Test retrieving result when none exists."""
        with app.test_request_context():
            assert session_service.retrieve_result() is None

    def test_clear_result(self, app, session_service, sample_table_data):
        """Test clearing result from session."""
        with app.test_request_context():
            session_service.store_result('<table></table>', sample_table_data)
            assert session_service.has_result()

            session_service.clear_result()
            assert not session_service.has_result()


class TestSessionServiceLanguage:
    """Tests for SessionService language management."""

    @pytest.mark.parametrize("lang_code,expected", [
        ('hu', 'hu'),
        ('en', 'en'),
        ('de', 'de'),
    ])
    def test_set_and_get_language(self, app, session_service, lang_code, expected):
        """Test setting and getting language preference."""
        with app.test_request_context():
            session_service.set_language(lang_code)
            assert session['lang'] == expected
            assert session_service.get_language() == expected
            assert session_service.has_language()

    def test_get_language_default(self, app, session_service):
        """Test getting language returns default when not set."""
        with app.test_request_context():
            assert not session_service.has_language()
            assert session_service.get_language() == SessionService.DEFAULT_LANGUAGE


class TestSessionServiceClear:
    """Tests for SessionService clear operations."""

    def test_clear_session_preserves_language(self, app, session_service, sample_form_data, sample_table_data):
        """Test clearing all session data preserves language preference."""
        with app.test_request_context():
            # Set all session data
            session_service.store_form_data(sample_form_data)
            session_service.store_result('<table></table>', sample_table_data)
            session_service.set_language('hu')

            # Clear session
            session_service.clear_session()

            # Check form data and result are cleared, language preserved
            assert not session_service.has_form_data()
            assert not session_service.has_result()
            assert session_service.get_language() == 'hu'

    def test_clear_session_when_empty(self, app, session_service):
        """Test clearing session when already empty."""
        with app.test_request_context():
            session_service.clear_session()  # Should not raise exception
            assert not session_service.has_form_data()
            assert not session_service.has_result()


class TestSessionServiceSize:
    """Tests for SessionService size tracking."""

    @pytest.mark.parametrize("setup_data,min_expected_size", [
        (lambda s: None, 0),  # Empty
        (lambda s: s.store_form_data({'filename': 'test.csv'}), 20),  # With form data
        (lambda s: (
            s.store_form_data({'filename': 'test.csv'}),
            s.set_language('en')
        ), 20),  # With multiple data
    ])
    def test_get_session_size(self, app, session_service, setup_data, min_expected_size):
        """Test session size calculation."""
        with app.test_request_context():
            setup_data(session_service)
            size = session_service.get_session_size()
            assert size >= min_expected_size

    def test_get_session_size_large_result(self, app, session_service):
        """Test session size with large HTML result."""
        with app.test_request_context():
            large_html = '<table>' + '<tr><td>data</td></tr>' * 1000 + '</table>'
            table_data = {
                'headers': ['Category'],
                'rows': [[{'data': 'Test', 'sort': 'test'}] for _ in range(1000)]
            }
            session_service.store_result(large_html, table_data)
            assert session_service.get_session_size() > 10000


class TestSessionServiceIntegration:
    """Integration tests for SessionService."""

    def test_full_workflow(self, app, session_service, sample_form_data, sample_table_data):
        """Test complete workflow: store form, process, store result, retrieve, clear."""
        with app.test_request_context():
            # Store form data
            session_service.store_form_data(sample_form_data)
            assert session_service.has_form_data()

            # Retrieve form data
            retrieved_form = session_service.retrieve_form_data()
            assert retrieved_form.filename == 'test.csv'
            assert retrieved_form.verbose is True

            # Store and retrieve result
            html_result = '<table><tr><th>Category</th><th>Amount</th></tr></table>'
            session_service.store_result(html_result, sample_table_data)
            assert session_service.has_result()

            result = session_service.retrieve_result()
            retrieved_html, retrieved_table = result
            assert 'Category' in retrieved_html
            assert retrieved_table.headers == ['Category', 'Amount']

            # Clear session
            session_service.clear_session()
            assert not session_service.has_form_data()
            assert not session_service.has_result()

    def test_session_isolation(self, app):
        """Test that different SessionService instances share Flask session."""
        with app.test_request_context():
            service1 = SessionService()
            service2 = SessionService()

            service1.store_form_data({'filename': 'test.csv'})
            retrieved = service2.retrieve_form_data()

            assert retrieved is not None
            assert retrieved.filename == 'test.csv'
