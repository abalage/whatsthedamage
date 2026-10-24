"""API contract fixture drift detection.

The frontend test suite asserts its TypeScript types against the
checked-in OpenAPI component schemas in
frontend/test/fixtures/api-contract-schemas.json. This test fails
when the backend's generated schema no longer matches the fixture,
so a backend contract change forces an explicit regeneration
(make api-contract) and the frontend test then surfaces the drift.
"""

import json
import os

from whatsthedamage.api.v2.schema import get_openapi_schema

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
FIXTURE_PATH = os.path.join(
    PROJECT_ROOT, 'frontend', 'test', 'fixtures', 'api-contract-schemas.json'
)


class TestApiContractFixture:
    """Test suite for the checked-in API contract fixture."""

    def test_fixture_matches_generated_schema(self):
        """The checked-in fixture is exactly the generated OpenAPI
        components; on mismatch regenerate with `make api-contract`."""
        generated = get_openapi_schema()['components']['schemas']

        with open(FIXTURE_PATH, encoding='utf-8') as handle:
            fixture = json.load(handle)

        assert fixture == generated, (
            'The API contract fixture is out of date with the backend '
            'OpenAPI schema. Regenerate it with `make api-contract` and '
            'check whether the frontend types in src/types/ need to '
            'follow the contract change.'
        )

    def test_fixture_exists(self):
        """The fixture file is present in the repository."""
        assert os.path.isfile(FIXTURE_PATH)
