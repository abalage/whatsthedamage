# API Style Guide

This document defines the conventions and best practices for API development in What's the Damage. All new endpoints must follow these guidelines to ensure consistency, type safety, and maintainability.

---

## 1. Response Format Conventions

### 1.1 Standard Response Structure

All API v2 endpoints **MUST** return Pydantic models defined in `src/whatsthedamage/models/api_responses.py`.

**Key Principles:**
- Every endpoint returns a strongly-typed Pydantic model
- Response structures are documented via Pydantic model docstrings
- Frontend TypeScript interfaces mirror backend Pydantic models exactly

### 1.2 Naming Conventions

| Entity Type | Convention | Example |
|------------|------------|---------|
| Response DTO (Python) | `{EndpointName}ApiResponse` | `DetailedResponse`, `ResultsApiResponse` |
| TypeScript Interface | Match Python DTO name exactly | `DetailedResponse`, `ResultsApiResponse` |
| Backend Endpoint | snake_case | `/api/v2/process`, `/api/v2/recalculate_statistics` |
| Frontend Function | camelCase | `processTransactions`, `fetchResults` |
| Type File | snake_case | `api_responses.py`, `api.ts` |

### 1.3 Response Field Naming

| Field Type | Convention | Example |
|-----------|------------|---------|
| IDs | snake_case | `result_id`, `account_id`, `category_id` |
| Timestamps | snake_case | `processing_time`, `timestamp` |
| Flags | snake_case | `ml_enabled`, `is_calculated` |
| Arrays | Plural noun | `data`, `accounts`, `highlights` |
| Objects | Singular noun | `metadata`, `accounts_data` |

---

## 2. Response Types

### 2.1 Success Responses

All successful responses must include the requested data and relevant metadata.

**Required Fields by Endpoint Type:**

| Endpoint Type | Required Fields |
|--------------|----------------|
| Processing (`/process`) | `data: AggregatedRow[]`, `metadata: ProcessingMetadata` |
| Results (`/results/{id}`) | `result_id`, `accounts_data`, `drilldown_urls_by_account` |
| Drilldown | `result_id`, `account_id`, `account_name`, `data`, `(category_id OR month_id)` |
| Recalculate | `status`, `result_id`, `highlights`, `algorithms`, `direction` |

### 2.2 Error Responses

All error responses **MUST** use the `ErrorApiResponse` format:

```json
{
  "code": 400,
  "message": "Human-readable error description",
  "details": { ... }  // optional, additional context
}
```

**HTTP Status Code Mapping:**

| Status Code | Error Type | Example |
|------------|------------|---------|
| 400 | Bad Request | Missing required parameter, invalid input format |
| 404 | Not Found | Resource doesn't exist (invalid result_id) |
| 422 | Unprocessable Entity | Data validation failed (CSV parsing, date format) |
| 500 | Internal Server Error | Unexpected server-side failure |

**Backend Implementation (Python):**
```python
from whatsthedamage.models.api_responses import ErrorApiResponse
from whatsthedamage.api.helpers import handle_error

# In endpoint:
try:
    # ... processing logic
    return jsonify(response.model_dump())
except ValueError as e:
    return handle_error(e, 400)
```

**Frontend Handling (TypeScript):**
```typescript
import { ErrorApiResponse } from '../types/api';

try {
  const response = await fetchResults(resultId);
} catch (error) {
  if (error instanceof AppError) {
    const errorData: ErrorApiResponse = {
      code: error.context?.status || 500,
      message: error.message,
    };
    console.error('API Error:', errorData);
  }
}
```

---

## 3. Standard Response Envelope (Optional for New Endpoints)

For consistency across new API endpoints, the **recommended** approach is to use the standard response envelope format. This provides a consistent structure with metadata, hypermedia links, and timestamps.

### 3.1 Envelope Structure

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "request_id": "unique-request-identifier",
    "version": "v2",
    "api_version": "2.0",
    "timestamp": "2025-01-01T00:00:00Z"
  },
  "links": {
    "self": "/api/v2/endpoint",
    "doc": "/docs/api/v2/endpoint"
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### 3.2 When to Use Envelope

| Scenario | Use Envelope? | Rationale |
|----------|--------------|-----------|
| New endpoints | ✅ Yes (recommended) | Standardization, future-proofing |
| Existing endpoints | ❌ No | Backward compatibility |
| Drilldown endpoints | ❌ No | Already have well-defined formats |
| Error responses | ❌ No | Use `ErrorApiResponse` format |

### 3.3 Backend Implementation

```python
from whatsthedamage.models.api_responses import ApiEnvelope, SomeDataModel

@v2_bp.route('/new-endpoint', methods=['GET'])
def new_endpoint():
    payload = SomeDataModel(...)
    envelope = ApiEnvelope[SomeDataModel](
        status='success',
        data=payload,
        meta={
            'request_id': generate_request_id(),
            'version': 'v2',
            'api_version': '2.0'
        },
        links={
            'self': '/api/v2/new-endpoint',
            'doc': '/docs/api/v2/new-endpoint'
        }
    )
    return jsonify(envelope.model_dump())
```

### 3.4 Frontend Implementation

```typescript
import { ApiEnvelope, fetchWithEnvelope, fetchEnvelope } from '../js/api';

// Get just the data (unwrapped)
const data = await fetchWithEnvelope<MyData>('/api/v2/new-endpoint');

// Get full envelope with metadata and links
const envelope = await fetchEnvelope<MyData>('/api/v2/new-endpoint');
console.log(envelope.meta.request_id);
console.log(envelope.links.self);
```

---

## 4. Validation Requirements

### 4.1 Backend Validation

- ✅ All backend endpoints **MUST** validate their responses using Pydantic
- ✅ All request parameters **MUST** be validated
- ✅ All file uploads **MUST** be validated (MIME type, size, content)
- ✅ Response models **MUST** be defined in `models/api_responses.py`

**Example:**
```python
from pydantic import BaseModel, Field
from typing import List

class DetailedResponse(BaseModel):
    """Response from POST /api/v2/process."""
    data: List[AggregatedRow] = Field(..., description="Aggregated transaction data")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "metadata": {"result_id": "", "row_count": 0, "processing_time": 0.0, "ml_enabled": False}
            }
        }
```

### 4.2 Frontend Validation

- ✅ All frontend API functions **MUST** have TypeScript return type annotations
- ✅ All frontend API functions **MUST** have JSDoc comments
- ✅ TypeScript interfaces **MUST** mirror Pydantic models exactly
- ✅ All types **MUST** be exported from `frontend/src/types/api.ts`

**Example:**
```typescript
/**
 * Response from POST /api/v2/process
 *
 * Contains processed transaction data grouped by category and month,
 * plus processing metadata.
 */
export interface DetailedResponse {
  data: AggregatedRow[];
  metadata: ProcessingMetadata;
}

/**
 * Process transactions via API
 *
 * @param formData - Form data containing CSV and config
 * @returns Promise with DetailedResponse containing aggregated transaction data
 * @throws AppError if processing fails
 */
export async function processTransactions(
  formData: FormData
): Promise<DetailedResponse> {
  // ... implementation
}
```

---

## 5. Testing Requirements

### 5.1 Contract Tests (Backend)

Each endpoint **MUST** have contract tests in `tests/api/v2/test_contract.py` that verify:

- [ ] Response structure matches the Pydantic model
- [ ] All required fields are present
- [ ] Field types are correct
- [ ] Response can be parsed by the Pydantic model

**Example Test:**
```python
def test_process_returns_valid_schema(client: FlaskClient):
    response = client.post('/api/v2/process', data={'csv_file': sample_csv})
    assert response.status_code == 200
    
    data = response.get_json()
    validated = DetailedResponse.model_validate(data)
    
    assert validated.data is not None
    assert validated.metadata.result_id is not None
```

### 5.2 Pydantic Model Tests

Each Pydantic model **MUST** have validation tests that verify:

- [ ] Valid data passes validation
- [ ] Invalid data (missing required fields) fails validation

**Example Test:**
```python
def test_process_api_response_model_structure():
    from pydantic import ValidationError
    
    # Valid data should pass
    valid_data = {
        'data': [],
        'metadata': {
            'result_id': 'test-id',
            'row_count': 0,
            'processing_time': 0.0,
            'ml_enabled': False,
        }
    }
    DetailedResponse.model_validate(valid_data)
    
    # Missing required fields should fail
    invalid_data = {'data': []}  # Missing metadata
    with pytest.raises(ValidationError):
        DetailedResponse.model_validate(invalid_data)
```

### 5.3 Integration Tests (Frontend)

Frontend integration tests **SHOULD** be created in `frontend/test/api/` to verify:

- [ ] API functions return correctly typed responses
- [ ] Error handling works as expected
- [ ] Type guards properly validate responses

---

## 6. Backward Compatibility

### 6.1 Legacy Types

For backward compatibility during the transition period, legacy type aliases are provided:

```typescript
// In frontend/src/types/api.ts
export type ProcessResponse = ProcessingResponse;  // Old name
export type ResultsResponseV2 = ResultsApiResponse;  // Old name
export type CategoryMonthsResponse = CategoryMonthsApiResponse;
export type MonthCategoriesResponse = MonthCategoriesApiResponse;
export type CategoryMonthTransactionsResponse = CategoryMonthTransactionsApiResponse;
```

**Migration Path:**
1. New code should use the new type names (`DetailedResponse`, etc.)
2. Legacy code can continue using the old names via aliases
3. Aliases will be deprecated in a future release

### 6.2 Breaking Changes

The following breaking changes were introduced to standardize the API contract:

| Change | Old Behavior | New Behavior | Migration |
|--------|-------------|--------------|-----------|
| Response types | Inconsistent dict structures | Pydantic models | Update frontend to use new types |
| `result_id` location | Root level (sometimes) | Always in `metadata` | Update to use `metadata.result_id` |
| Error format | `{error, status}` | `{code, message, details?}` | Update error handling |

---

## 7. Best Practices

### 7.1 Backend

**Do:**
- ✅ Use Pydantic models for all responses
- ✅ Add docstrings to all models and endpoints
- ✅ Validate all inputs and outputs
- ✅ Use dependency injection for services
- ✅ Return `jsonify(model.model_dump())` for Pydantic models
- ✅ Handle errors consistently with `handle_error()`

**Don't:**
- ❌ Return raw dicts from endpoints
- ❌ Skip validation for "internal" endpoints
- ❌ Expose database models directly
- ❌ Use generic `Any` types in Pydantic models

### 7.2 Frontend

**Do:**
- ✅ Use TypeScript interfaces for all API responses
- ✅ Add JSDoc comments to all API functions
- ✅ Mirror backend Pydantic model names exactly
- ✅ Handle errors with `AppError` class
- ✅ Use typed return values for all API functions

**Don't:**
- ❌ Use `any` or `unknown` for API response types
- ❌ Skip error handling
- ❌ Make API calls directly from components (use stores)
- ❌ Ignore type mismatches

### 7.3 Both

**Do:**
- ✅ Keep types in sync between backend and frontend
- ✅ Document all fields and their purposes
- ✅ Use consistent naming conventions
- ✅ Test response schemas with contract tests

**Don't:**
- ❌ Make assumptions about response structures
- ❌ Change types without updating both sides
- ❌ Skip documentation

---

## 8. Example: Complete Endpoint Implementation

### 8.1 Backend (Python/Flask)

```python
# models/api_responses.py
from pydantic import BaseModel, Field
from typing import List
from .dt_models import AggregatedRow, ProcessingMetadata

class DetailedResponse(BaseModel):
    """Response from POST /api/v2/process."""
    data: List[AggregatedRow] = Field(..., description="Aggregated transaction data")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")


# api/v2/endpoints.py
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest
from ..models.api_responses import DetailedResponse, ErrorApiResponse
from ..api.helpers import validate_csv_file, save_uploaded_files, cleanup_files

@v2_bp.route('/process', methods=['POST'])
def process_transactions():
    """Process CSV transaction file and return detailed transaction data."""
    try:
        csv_file = validate_csv_file()
        csv_path, config_path = save_uploaded_files(csv_file, None)
        
        # Process data
        result = processing_service.process_with_details(
            csv_path, config_path, request.args
        )
        
        cleanup_files(csv_path, config_path)
        
        response = DetailedResponse(
            data=result.data[''].data,  # Extract aggregated rows
            metadata=result.metadata
        )
        
        return jsonify(response.model_dump())
        
    except ValueError as e:
        return handle_error(e, 400)
```

### 8.2 Frontend (TypeScript)

```typescript
// frontend/src/types/api.ts
export interface AggregatedRow {
  row_id: string;
  category: string;
  total: DisplayRawField;
  date: DateField;
  details: DetailRow[];
}

export interface ProcessingMetadata {
  result_id: string;
  row_count: number;
  processing_time: number;
  ml_enabled: boolean;
  date_range?: string;
}

export interface DetailedResponse {
  data: AggregatedRow[];
  metadata: ProcessingMetadata;
}

// frontend/src/js/api.ts
export async function processTransactions(
  formData: FormData
): Promise<DetailedResponse> {
  const response = await fetch(`${API_BASE_URL}/process`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new AppError(
      errorData.message ?? errorData.error ?? 'Transaction processing failed',
      { status: response.status }
    );
  }

  return await response.json();
}

// frontend/src/pages/Results.vue (usage)
import { processTransactions } from '../js/api';
import type { DetailedResponse, AggregatedRow } from '../types/api';

const onSubmit = async (formData: FormData) => {
  try {
    const response: DetailedResponse = await processTransactions(formData);
    console.log('Result ID:', response.metadata.result_id);
    console.log('Rows processed:', response.metadata.row_count);
    console.log('Data:', response.data);
  } catch (error) {
    if (error instanceof AppError) {
      console.error('Error:', error.message);
    }
  }
};
```

---

## 9. Checklist for New Endpoints

Before merging new API endpoints, verify the following:

### Backend
- [ ] Pydantic response model defined in `models/api_responses.py`
- [ ] Model has docstring explaining its purpose
- [ ] Model has example data in `json_schema_extra`
- [ ] Endpoint returns `jsonify(model.model_dump())`
- [ ] Error handling uses `handle_error()` or returns `ErrorApiResponse`
- [ ] All parameters validated
- [ ] Contract test added to `tests/api/v2/test_contract.py`
- [ ] Pydantic model validation test added

### Frontend
- [ ] TypeScript interface defined in `frontend/src/types/api.ts`
- [ ] Interface matches Pydantic model exactly
- [ ] Interface has JSDoc comments
- [ ] Interface exported
- [ ] API function has TypeScript return type annotation
- [ ] API function has JSDoc comments
- [ ] API function handles errors with `AppError`
- [ ] Integration test added (optional but recommended)

### Documentation
- [ ] Endpoint documented in `docs/api-first-architecture.md`
- [ ] Response format documented
- [ ] Example requests/responses documented
- [ ] Error scenarios documented

---

## 10. References

- [API-First Architecture Documentation](api-first-architecture.md)
- [Backend Models](src/whatsthedamage/models/api_responses.py)
- [Frontend Types](frontend/src/types/api.ts)
- [Contract Tests](tests/api/v2/test_contract.py)
