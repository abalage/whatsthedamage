import os
from flask import session, current_app
from whatsthedamage.controllers.routes import clear_upload_folder
from io import BytesIO
from .helpers import create_sample_csv_from_fixture  # Import the function


def mock_processing_service(monkeypatch, process_with_details_fn=None):
    """Helper to mock ProcessingService via dependency injection."""
    class MockService:
        def process_with_details(self, **kwargs):
            if process_with_details_fn:
                return process_with_details_fn(**kwargs)
            return {}

    monkeypatch.setattr('whatsthedamage.controllers.routes_helpers._get_processing_service', lambda: MockService())


def get_csrf_token(client):
    response = client.get('/')
    csrf_token = None
    for line in response.data.decode().split('\n'):
        if 'csrf_token' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    return csrf_token


def read_file(file_path):
    with open(file_path, 'rb') as f:
        return f.read()


def print_form_errors(client):
    with client.session_transaction() as sess:
        form_errors = sess.get('_flashes', [])
        if form_errors:
            print("Form errors:", form_errors)
        else:
            e = sess.get('e', 'No error message found')
            print("Error:", e)


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<form' in response.data


def test_process_route(client, monkeypatch, csv_rows, mapping, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result({'balance': 100.0})

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    # Create a minimal config file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
        config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
        config_file_path = config_file.name

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file(config_file_path)), 'config.yml'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
    }

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    response = client.post('/process', data=data, content_type='multipart/form-data')

    if response.status_code != 200:
        print_form_errors(client)
        # Also check if it's a redirect and print the location
        if response.status_code == 302:
            print("Redirect location:", response.headers.get('Location'))

    assert response.status_code == 200
    # Check that form data is stored in session
    with client.session_transaction() as sess:
        assert 'form_data' in sess

    os.remove(sample_csv_path)


def test_clear_route(client):
    csrf_token = get_csrf_token(client)

    with client.session_transaction() as sess:
        sess['form_data'] = {'some': 'data'}
    response = client.post('/clear', data={'csrf_token': csrf_token})

    if response.status_code != 302:
        print_form_errors(client)

    assert response.status_code == 302
    assert 'form_data' not in session


def test_clear_upload_folder(client):
    with client.application.app_context():
        upload_folder = current_app.config['UPLOAD_FOLDER']
        test_file_path = os.path.join(upload_folder, 'test.txt')
        with open(test_file_path, 'w') as f:
            f.write('test content')

        clear_upload_folder()
        assert not os.path.exists(test_file_path)


def test_process_route_invalid_data(client, monkeypatch, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result()

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)

    # Create a minimal config file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
        config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
        config_file_path = config_file.name

    data = {
        'csrf_token': csrf_token,
        'config': (BytesIO(read_file(config_file_path)), 'config.yml')
        # Missing other required fields
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to validation failure


def test_process_route_missing_file(client, monkeypatch, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result()

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)

    # Create a minimal config file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
        config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
        config_file_path = config_file.name

    data = {
        'csrf_token': csrf_token,
        'config': (BytesIO(read_file(config_file_path)), 'config.yml'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to missing file


def test_process_route_missing_config(client, monkeypatch, csv_rows, mapping, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result()

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'ml': True,  # <-- ML mode enabled, config can be missing
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 200:
        print_form_errors(client)
    assert response.status_code == 200

    os.remove(sample_csv_path)


def test_process_route_invalid_end_date(client, monkeypatch, csv_rows, mapping, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result()

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    # Create a minimal config file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
        config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
        config_file_path = config_file.name

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file(config_file_path)), 'config.yml'),
        'start_date': '2023-01-01',
        'end_date': 'invalid-date',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to invalid end date format
    assert 'form_data' not in session

    os.remove(sample_csv_path)


def test_process_route_invalid_date(client, monkeypatch, csv_rows, mapping, mock_processing_service_result):
    def mock_process_with_details(**kwargs):
        return mock_processing_service_result()

    mock_processing_service(monkeypatch, process_with_details_fn=mock_process_with_details)

    csrf_token = get_csrf_token(client)
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    # Create a minimal config file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
        config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
        config_file_path = config_file.name

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file(config_file_path)), 'config.yml'),
        'start_date': 'invalid-date',
        'end_date': '2023-12-31',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to invalid start date format
    assert 'form_data' not in session

    os.remove(sample_csv_path)
