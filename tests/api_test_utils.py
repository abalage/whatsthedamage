"""
Test utilities for API unit tests.

Provides helper functions and mock factories to reduce test boilerplate
and make tests more readable and maintainable.
"""
from io import BytesIO
from typing import Dict, List, Any, Optional
from unittest.mock import Mock


class MockProcessingService:
    """Mock ProcessingService for testing with simplified result builders."""

    def __init__(self):
        self.process_summary = Mock()
        self.process_with_details = Mock()

    @staticmethod
    def create_summary_result(categories: Dict[str, float], row_count: int = 0) -> Dict[str, Any]:
        """Create a summary result structure for v1 API.

        Args:
            categories: Dictionary of category -> amount
            row_count: Number of rows processed

        Returns:
            Result dict matching ProcessingService.process_summary output
        """
        return {
            'data': categories,
            'metadata': {'row_count': row_count}
        }

    @staticmethod
    def create_detailed_result(rows: Optional[List[Dict]] = None, row_count: int = 0) -> Dict[str, Any]:
        """Create a detailed result structure for v2 API.

        Args:
            rows: List of aggregated row dictionaries (category, total, month, details)
            row_count: Number of rows processed

        Returns:
            Result dict matching ProcessingService.process_with_details output
        """
        if rows is None:
            rows = []

        class MockDataTablesResponse:
            def __init__(self, data):
                self.data = data

        return {
            'data': MockDataTablesResponse(rows),
            'metadata': {'row_count': row_count}
        }

    @staticmethod
    def create_detail_row(category: str, total: float, merchant: str = 'Test Merchant') -> Dict[str, Any]:
        """Create a single aggregated row for v2 API responses.

        Args:
            category: Transaction category
            total: Total amount
            merchant: Merchant name for details

        Returns:
            Aggregated row dict with category, total, month, and details
        """
        return {
            'category': category,
            'total': {'display': f'{total:.2f}', 'raw': total},
            'month': {'display': 'January 2023', 'timestamp': 1672531200},
            'details': [
                {
                    'date': {'display': '2023-01-01', 'timestamp': 1672531200},
                    'amount': {'display': f'{total:.2f}', 'raw': total},
                    'merchant': merchant
                }
            ]
        }


class APITestClient:
    """Wrapper around Flask test client with helper methods for API testing."""

    def __init__(self, client):
        self.client = client

    def post_csv(self, endpoint: str, csv_file: tuple, **params) -> Any:
        """Post CSV file to an API endpoint.

        Args:
            endpoint: API endpoint path (e.g., '/api/v1/process')
            csv_file: Tuple of (BytesIO, filename)
            **params: Additional form parameters

        Returns:
            Flask response object
        """
        data = {'csv_file': csv_file, **params}
        return self.client.post(endpoint, data=data, content_type='multipart/form-data')

    def assert_success(self, response, expected_row_count: Optional[int] = None) -> Dict:
        """Assert successful response and return parsed JSON.

        Args:
            response: Flask response object
            expected_row_count: Optional expected row count to verify

        Returns:
            Parsed JSON response data
        """
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'metadata' in data

        if expected_row_count is not None:
            assert data['metadata']['row_count'] == expected_row_count

        return data

    def assert_error(self, response, expected_status: int, expected_message_contains: Optional[str] = None) -> Dict:
        """Assert error response with expected status code.

        Args:
            response: Flask response object
            expected_status: Expected HTTP status code
            expected_message_contains: Optional substring to check in error message

        Returns:
            Parsed JSON error response
        """
        assert response.status_code == expected_status
        data = response.get_json()
        assert 'code' in data
        assert 'message' in data
        assert data['code'] == expected_status

        if expected_message_contains:
            assert expected_message_contains.lower() in data['message'].lower()

        return data


def create_csv_bytes(rows: List[List[str]], headers: Optional[List[str]] = None) -> BytesIO:
    """Create CSV file content as BytesIO.

    Args:
        rows: List of rows, each row is a list of string values
        headers: Optional header row

    Returns:
        BytesIO ready for upload
    """
    if headers is None:
        headers = ['date', 'amount', 'partner', 'type', 'currency']

    lines = [','.join(headers)]
    lines.extend([','.join(row) for row in rows])
    content = '\n'.join(lines).encode('utf-8')

    return BytesIO(content)
