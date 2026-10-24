"""Generate the API contract fixture consumed by the frontend tests.

Dumps the OpenAPI component schemas of the backend API v2 into
frontend/test/fixtures/api-contract-schemas.json. The frontend test
suite asserts its hand-mirrored TypeScript types against this
fixture, so backend contract changes surface at frontend gate time.

Regenerate with:

    make api-contract

after intentionally changing an API model.
"""

import json
import os
import sys

# Make the project root importable regardless of the caller's cwd
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from whatsthedamage.api.v2.schema import get_openapi_schema  # noqa: E402

FIXTURE_PATH = os.path.join(
    PROJECT_ROOT, 'frontend', 'test', 'fixtures', 'api-contract-schemas.json'
)


def main() -> None:
    """Write the OpenAPI component schemas to the fixture file."""
    schema = get_openapi_schema()
    components = schema['components']['schemas']

    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, 'w', encoding='utf-8') as handle:
        json.dump(components, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(f'Wrote {FIXTURE_PATH} ({len(components)} component schemas)')


if __name__ == '__main__':
    main()
