import os
import pytest
from flask import session, current_app
from whatsthedamage.controllers.routes import bp, clear_upload_folder
from io import BytesIO
from whatsthedamage.app import create_app
from .helpers import create_sample_csv_from_fixture  # Import the function


@pytest.fixture
def client():
    config = {
        'TESTING': True,
        'UPLOAD_FOLDER': '/tmp/uploads'
    }
    app = create_app()
    app.config.from_mapping(config)
    app.register_blueprint(bp, name='test_bp')
    with app.test_client() as client:
        with app.app_context():
            yield client


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


def test_process_route(client, monkeypatch, csv_rows, mapping):
    def mock_process_csv(args):
        return '<table class="table table-bordered table-striped"></table>'

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    # Create sample CSV file using the imported function
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
    }

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    response = client.post('/process', data=data, content_type='multipart/form-data')

    if response.status_code != 200:
        print_form_errors(client)

    assert response.status_code == 200
    assert b'<table class="table table-bordered table-striped">' in response.data

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


def test_process_route_invalid_data(client, monkeypatch):
    def mock_process_csv(args):
        return "<table class='dataframe'></table>"

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    data = {
        'csrf_token': csrf_token,
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default')
        # Missing other required fields
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to validation failure


def test_process_route_missing_file(client, monkeypatch):
    def mock_process_csv():
        return "<table class='dataframe'></table>"

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    data = {
        'csrf_token': csrf_token,
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to missing file


def test_process_route_missing_config(client, monkeypatch, csv_rows, mapping):
    def mock_process_csv(args):
        return "<table class='dataframe'></table>"

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    # Create sample CSV file using the imported function
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 200:
        print_form_errors(client)
    assert response.status_code == 200

    os.remove(sample_csv_path)


def test_process_route_invalid_end_date(client, monkeypatch, csv_rows, mapping):
    def mock_process_csv(args):
        return "<table class='dataframe'></table>"

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    # Create sample CSV file using the imported function
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default'),
        'start_date': '2023-01-01',
        'end_date': 'invalid-date',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to invalid end date format
    assert 'form_data' not in session

    os.remove(sample_csv_path)


def test_download_route_with_result(client, monkeypatch, csv_rows, mapping):
    def mock_process_csv(args):
        return ("<table class='dataframe'><tr><td>Unnamed: 0</td>"
                "<td>2023.01.01 - 2023.12.31</td></tr><tr><td>balance</td>"
                "<td>0.0</td></tr></table>")

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    # Create sample CSV file using the imported function
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default'),
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'no_currency_format': True,
    }
    client.post('/process', data=data, content_type='multipart/form-data')

    response = client.get('/download')
    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == 'attachment; filename=result.csv'
    assert response.headers['Content-Type'] == 'text/csv'
    assert b'Unnamed: 0,2023.01.01 - 2023.12.31\nbalance,0.0\n' in response.data

    os.remove(sample_csv_path)


def test_process_route_invalid_date(client, monkeypatch, csv_rows, mapping):
    def mock_process_csv(args):
        return "<table class='dataframe'></table>"

    monkeypatch.setattr('whatsthedamage.controllers.routes.process_csv', mock_process_csv)

    csrf_token = get_csrf_token(client)

    # Create sample CSV file using the imported function
    sample_csv_path = create_sample_csv_from_fixture(csv_rows, mapping)

    data = {
        'csrf_token': csrf_token,
        'filename': (BytesIO(read_file(sample_csv_path)), 'sample.csv'),
        'config': (BytesIO(read_file('config.yml.default')), 'config.yml.default'),
        'start_date': 'invalid-date',
        'end_date': '2023-12-31',
    }
    response = client.post('/process', data=data, content_type='multipart/form-data')
    if response.status_code != 302:
        print_form_errors(client)
    assert response.status_code == 302  # Expecting a redirect due to invalid start date format
    assert 'form_data' not in session

    os.remove(sample_csv_path)
