# API-First Architecture: Frontend ↔ Backend Communication

This document explains the **API-first architecture** pattern used in What's the Damage, focusing on the roles and responsibilities of the frontend API client (`frontend/src/js/api.ts`) and the backend REST controller (`src/whatsthedamage/api/v2/endpoints.py`).

## Table of Contents

- [Core Responsibility Split](#core-responsibility-split)
- [Frontend: api.ts - Client-Side Contract Implementation](#frontend-api.ts---client-side-contract-implementation)
  - [Infrastructure Functions](#1-infrastructure-functions)
  - [Endpoint Functions](#2-endpoint-functions)
  - [Multipart Handling Exception](#3-multipart-handling-exception)
- [Backend: endpoints.py - Server-Side Contract Implementation](#backend-endpoints.py---server-side-contract-implementation)
  - [Service Delegation Pattern](#1-service-delegation-pattern)
  - [Route Functions](#2-route-functions)
  - [Request Lifecycle](#3-request-lifecycle)
- [Interaction Patterns](#interaction-patterns)
  - [Pattern 1: File Processing](#pattern-1-file-processing)
  - [Pattern 2: Results Retrieval](#pattern-2-results-retrieval)
  - [Pattern 3: Drilldown Navigation](#pattern-3-drilldown-navigation)
  - [Pattern 4: Statistics Recalculation](#pattern-4-statistics-recalculation)
- [Key Design Principles](#key-design-principles)
- [Data Flow Comparison](#data-flow-comparison)
- [Type Mapping](#type-mapping)
- [Contract Summary](#contract-summary)

---

## Core Responsibility Split

| Layer | `frontend/src/js/api.ts` | `backend/src/whatsthedamage/api/v2/endpoints.py` |
|-------|--------------------------|--------------------------------------------------|
| **Role** | API Client / Service Proxy | REST Controller |
| **Primary Concern** | Browser HTTP communication | Route handling + business logic delegation |
| **Type System** | TypeScript interfaces | Python Pydantic models + dicts |

---

## Frontend: `api.ts` - Client-Side Contract Implementation

**Core Purpose**: Abstract HTTP communication with type safety and error handling.

The frontend API module serves as a **type-safe client** that encapsulates all communication with the backend REST API. It provides a clean abstraction layer between Vue components and HTTP requests.

### 1. Infrastructure Functions (Building Blocks)

These are the foundational utilities that handle the mechanics of HTTP communication:

```typescript
// Low-level: fetch + JSON parsing + response wrapping
export async function fetchApi<T>(url: string, options: RequestInit = {}): Promise<ApiResponse<T>>

// Mid-level: throws AppError on non-OK responses
export async function fetchWithErrorHandling<T>(url: string, options: RequestInit = {}): Promise<T>

// High-level: JSON POST convenience
export async function postData<T>(url: string, data: unknown): Promise<T>

// URL builder: API_BASE_URL + endpoint
export function getApiUrl(endpoint: string): string
```

**Purpose**: Provide reusable, type-safe primitives for HTTP operations that can be composed into endpoint-specific functions.

### 2. Endpoint Functions

Each backend route has a corresponding frontend function with:
- Strong TypeScript return types (`ProcessResponse`, `ResultsResponseV2`, etc.)
- Proper error handling via `AppError`
- Parameter validation
- Documentation via JSDoc

| Function | HTTP | Backend Endpoint | Special Notes |
|----------|------|------------------|---------------|
| `processTransactions(formData)` | POST | `/api/v2/process` | **Multipart**: No Content-Type header, uses raw `fetch` |
| `fetchResults(resultId)` | GET | `/api/v2/results/{id}` | Returns typed `ResultsResponseV2` |
| `fetchAccountResults(resultId)` | GET | `/api/v2/results/{id}` | For details page, same endpoint as fetchResults |
| `fetchCategoryMonths(params)` | GET | `/api/v2/results/{r}/accounts/{a}/categories/{c}/months` | Drilldown endpoint |
| `fetchMonthCategories(params)` | GET | `/api/v2/results/{r}/accounts/{a}/months/{m}/categories` | Drilldown endpoint |
| `fetchCategoryMonthTransactions(params)` | GET | `/api/v2/results/{r}/accounts/{a}/categories/{c}/months/{m}/transactions` | Drilldown endpoint |
| `recalculateStatistics(resultId, algorithms, direction)` | POST | `/api/v2/recalculate-statistics` | JSON payload with algorithm settings |

**Design Pattern**: **Repository Pattern** - Each function acts as a repository method that fetches data from a specific API endpoint.

### 3. Multipart Handling Exception

The `processTransactions` function **bypasses** `fetchWithErrorHandling` because:

1. **Multipart Form Data**: Uses `FormData` object for file uploads (CSV and config files)
2. **Content-Type Restriction**: **Cannot** manually set `Content-Type` header - the browser must automatically add the `multipart/form-data` boundary parameter
3. **Error Response Variability**: Error responses may not always be JSON (fallback to `statusText`)

```typescript
export async function processTransactions(formData: FormData): Promise<ProcessResponse> {
  // Note: No Content-Type header - browser sets it with boundary
  const response = await fetch(`${API_BASE_URL}/process`, {
    method: 'POST',
    body: formData,
    // Content-Type is intentionally omitted
  });
  // ... error handling and response parsing
}
```

**Key Insight**: The frontend must respect HTTP specifications for multipart form data, which require special handling distinct from JSON APIs.

---

## Backend: `endpoints.py` - Server-Side Contract Implementation

**Core Purpose**: Define REST routes and orchestrate business logic through service delegation.

The backend endpoints module follows the **Controller** pattern in MVC architecture, handling HTTP requests and delegating business logic to specialized services.

### 1. Service Delegation Pattern

The backend uses **Dependency Injection** via factory functions to access services:

```python
_get_processing_service()        # ProcessingService - handles CSV processing
_get_cache_service()             # CacheService - manages cached results
_get_statistical_service()       # StatisticalService - computes IQR/Pareto highlights
_get_drilldown_response_service() # DrilldownResponseService - formats drilldown data
_get_response_builder_service()   # ResponseFormattingService - builds API responses
_get_file_upload_service()       # FileUploadService - validates and saves uploaded files
_get_id_mapping_service()        # IdMappingService - maps internal IDs to display names
_get_session_service()           # SessionService - manages user session data
_get_configuration_service()    # ConfigurationService - loads and manages app configuration
```

**Benefits**:
- **Single Responsibility**: Each service handles one domain concern
- **Testability**: Services can be mocked independently
- **Maintainability**: Changes to business logic don't affect route definitions
- **Loose Coupling**: Controllers don't contain business logic

### 2. Route Functions

Each route function follows a consistent pattern:

1. **Validate** request (files, parameters, JSON body)
2. **Delegate** to appropriate service
3. **Transform** service result to HTTP response
4. **Handle** errors consistently via `handle_error()`

| Route | HTTP Method | Service | Response Data |
|-------|-------------|---------|---------------|
| `/process` | POST | ProcessingService | JSON: processed transactions + metadata |
| `/results/<result_id>` | GET | CacheService + ResponseBuilder | JSON: cached results for frontend rendering |
| `/results/.../categories/.../months` | GET | DrilldownResponseService | JSON: category months aggregation |
| `/results/.../months/.../categories` | GET | DrilldownResponseService | JSON: month categories aggregation |
| `/results/.../categories/.../months/.../transactions` | GET | DrilldownResponseService | JSON: individual transaction details |
| `/recalculate-statistics` | POST | StatisticalService | JSON: updated statistical highlights |

### 3. Request Lifecycle

For most endpoints (GET endpoints):
```
HTTP Request
    ↓
Flask Route Matching (Blueprint @v2_bp.route)
    ↓
Request Validation (files, params, JSON)
    ↓
Service Instantiation (via factory functions)
    ↓
Business Logic Execution (in service methods)
    ↓
Result Caching (for drilldown navigation)
    ↓
Response Formatting (JSON with status code)
    ↓
HTTP Response
```

For `/api/v2/process` (POST with file upload):
```
HTTP Request
    ↓
Flask Route Matching (Blueprint @v2_bp.route)
    ↓
Request Validation (csv_file required, config_file optional)
    ↓
File Validation (validate_csv_file, get_config_file via FileUploadService)
    ↓
File Saving (save_uploaded_files to temporary storage)
    ↓
Service Instantiation (via factory functions)
    ↓
Business Logic Execution (ProcessingService.process_with_details)
    ↓
Result Caching (CacheService.set with result_id)
    ↓
Response Formatting (ResponseFormattingService.build_api_detailed_response)
    ↓
File Cleanup (cleanup_files in finally block)
    ↓
HTTP Response
```

---

## Interaction Patterns

The frontend and backend communicate through well-defined patterns for each use case.

### Pattern 1: File Processing

**User Action**: User uploads CSV file on the index page

```
Frontend: Index.vue
    │
    ▼ [User submits form with CSV + optional config]

frontend/src/js/api.ts::processTransactions(FormData)
    │
    ▼ [POST /api/v2/process]
    ▼ [Headers: none (browser sets Content-Type with boundary)]
    ▼ [Body: FormData with csv_file, config_file, params]

Backend: endpoints.py::process_transactions()
    │
    ▼ [Validate CSV file exists and is valid]
    ▼ [Parse request parameters (dates, filters, etc.)]
    ▼ [Save uploaded files temporarily]

    ▼ ProcessingService.process_with_details(...)
    │   │
    │   ▼ [Parse CSV file]
    │   ▼ [Categorize transactions]
    │   ▼ [Apply filters]
    │   ▼ [Return ProcessingResponse]
    │
    ▼ [Cache result with result_id]
    ▼ [Build API response with ResponseFormattingService]

    │
    ▼ [HTTP 200]
    ▼ [JSON: {data: AggregatedRow[], metadata: {result_id, row_count, processing_time, ml_enabled, date_range}}]

frontend/src/js/api.ts::processTransactions() [resolves with ProcessResponse]
    │
    ▼ [Extract result_id from response]
    ▼ [Show success message via FeedbackStore]

Frontend: Index.vue
    │
    ▼ [Navigate to /results?resultId={result_id}]

Results.vue
    │
    ▼ [Load and display processed results]
```

**Key Points**:
- Frontend handles file selection and form submission
- Backend validates, processes, caches, and returns results
- `result_id` is the link between processing and results retrieval

### Pattern 2: Results Retrieval

**User Action**: User navigates to results page or refreshes

```
Frontend: Results.vue (onMounted)
    │
    ▼ [Extract resultId from route query params]

frontend/src/js/api.ts::fetchResults(resultId)
    │
    ▼ [GET /api/v2/results/{resultId}]

Backend: endpoints.py::get_results(result_id)
    │
    ▼ [Lookup result in cache via CacheService]
    ▼ [If not found: return 404]

    ▼ ResponseFormattingService.format_processing_response_for_frontend()
    │   │
    │   ▼ [Transform internal data structures]
    │   ▼ [Add drilldown URLs]
    │   ▼ [Format for DataTables compatibility]
    │
    ▼ [HTTP 200]
    ▼ [JSON: {result_id, accounts_data, drilldown_urls_by_account, highlights}]

frontend/src/js/api.ts::fetchResults() [resolves with ResultsResponseV2]
    │
    ▼ [Store in Vue ref: resultsData.value]
    ▼ [Set window.highlights for cell highlighting]
    ▼ [Initialize DataTables via window.initMainPage()]

Frontend: Results.vue
    │
    ▼ [Render account tables with category/month matrix]
    ▼ [Apply highlight CSS classes to cells]
```

**Key Points**:
- Results are cached on backend after processing
- Frontend retrieves cached results by `result_id`
- Response includes pre-computed drilldown URLs for navigation

### Pattern 3: Drilldown Navigation

**User Action**: User clicks on a category, month, or cell in the results table

```
Frontend: Results.vue (cell click handler)
    │
    ▼ [Extract route params: resultId, accountId, categoryId, monthId]

frontend/src/composables/useDrilldownData.ts::useDrilldownData()
    │
    ▼ [Build endpoint URL from params]
    ▼ [Call fetchWithErrorHandling with full URL]

frontend/src/js/api.ts::fetchCategoryMonths(params)
    │
    ▼ [GET /api/v2/results/{r}/accounts/{a}/categories/{c}/months]

Backend: endpoints.py::get_category_months(result_id, account_id, category_id)
    │
    ▼ [Retrieve cached result via CacheService]
    ▼ [Validate result, account, category exist]

    ▼ DrilldownResponseService.get_category_months_response(...)
    │   │
    │   ▼ [Extract data for specific category]
    │   ▼ [Aggregate transactions by month]
    │   ▼ [Compute totals for each month]
    │   ▼ [Filter to requested category]
    │
    ▼ [HTTP 200]
    ▼ [JSON: {result_id, account_id, account_name, category_id, category_name, data, highlights}]

frontend/src/js/api.ts::fetchCategoryMonths() [resolves with CategoryMonthsResponse]
    │
    ▼ [Store in useDrilldownData state]
    ▼ [Set window.highlights]
    ▼ [Initialize DataTables]

Frontend: CategoryMonthsList.vue
    │
    ▼ [Render table with months and totals for category]
    ▼ [Apply cell highlights]
```

**Key Points**:
- Drilldown uses the same cached processing result
- Different endpoints provide different aggregation levels (category/month, month/category, cell/transaction)
- Each drilldown view can recalculate statistics independently

### Pattern 4: Statistics Recalculation

**User Action**: User changes statistical analysis settings (algorithms, direction)

```
Frontend: StatisticalControls.vue (recalculate button)
    │
    ▼ [Collect current settings: algorithms, direction]

frontend/src/js/api.ts::recalculateStatistics(resultId, algorithms, direction)
    │
    ▼ [POST /api/v2/recalculate-statistics]
    ▼ [Body: {result_id, algorithms: ['iqr', 'pareto'], direction: 'columns'}]

Backend: endpoints.py::recalculate_statistics()
    │
    ▼ [Validate JSON payload]
    ▼ [Extract: result_id, algorithms, direction]
    ▼ [Validate parameters]

    ▼ [Retrieve cached result via CacheService]
    ▼ [If not found: return 404]

    ▼ StatisticalService.compute_statistical_metadata(
          cached_result.data,
          algorithms=algorithms,
          direction=direction
      )
    │   │
    │   ▼ [Run IQR outlier detection]
    │   ▼ [Run Pareto analysis]
    │   ▼ [Identify excluded cells]
    │   ▼ [Return StatisticalMetadata]
    │
    ▼ [Convert highlights to dict format: {row_id: [type1, type2]}]
    ▼ [Update cache with new statistical metadata]

    ▼ [HTTP 200]
    ▼ [JSON: {status: 'success', result_id, highlights, algorithms, direction}]

frontend/src/js/api.ts::recalculateStatistics() [resolves with response]
    │
    ▼ [Update window.highlights with new highlights]
    ▼ [Call window.updateCellHighlights()]

Frontend: statistical-analysis.ts::updateCellHighlights()
    │
    ▼ [Remove all existing highlight classes]
    ▼ [Add new highlight classes based on response]

Frontend: Results.vue / Drilldown pages
    │
    ▼ [Cells display updated statistical highlights]
```

**Key Points**:
- Statistical analysis is re-computable with different settings
- Highlights are stored in cache and updated when recalculated
- Frontend re-applies CSS classes to reflect new statistical analysis

---

## Key Design Principles

| Principle | Frontend Implementation | Backend Implementation |
|-----------|-------------------------|------------------------|
| **Separation of Concerns** | API client only, no business logic | Route handling only, delegates to services |
| **Single Responsibility** | Each function handles one endpoint | Each route function handles one URL path |
| **Type Safety** | TypeScript generics + interfaces | Pydantic models + Python type hints |
| **Error Handling** | `AppError` with context passed to components | `handle_error()` returns proper HTTP status |
| **Dependency Injection** | Pinia stores for state management | Service factory functions for loose coupling |
| **DRY (Don't Repeat Yourself)** | Shared `fetchApi`/`fetchWithErrorHandling` utilities | Shared `handle_error` helper function |
| **Open/Closed Principle** | New endpoints can be added without modifying existing code | New routes can be added without modifying existing services |

---

## Data Flow Comparison

| Aspect | Frontend (`api.ts`) | Backend (`endpoints.py`) |
|--------|----------------------|--------------------------|
| **Request Initiation** | `fetch(url, {method, body, headers})` | Flask route decorator `@v2_bp.route()` |
| **Request Data** | `FormData` or JSON string | `request.files`, `request.get_json()`, `request.args` |
| **Response Handling** | `Promise<T>` with parsed JSON | `jsonify(data), HTTP_status_code` |
| **Validation** | Vue component validation (UI feedback) | Route-level validation (HTTP 400 errors) |
| **Errors** | `throw AppError` caught by components | `return handle_error(e)` returns HTTP error response |
| **Error Format** | `AppError` with `{message, status, url}` | `{code, message, details?}` JSON response |
| **Caching** | None (browser may cache HTTP responses) | `CacheService` stores processing results by `result_id` |
| **DTOs (Data Transfer Objects)** | TypeScript interfaces (`ProcessApiResponse`, `ResultsResponseV2`, etc.) | Pydantic models (`DetailedResponse`, `ProcessingResponse`) **and** Python dicts (for `/results`, `/recalculate-statistics`, drilldown endpoints) |
| **Asynchronous** | Native Promise-based async/await | Synchronous route handling (Flask is sync by default) |
| **Content-Type Handling** | `fetchApi` always sets `Content-Type: application/json`; `processTransactions` uses raw `fetch` to allow browser to set `multipart/form-data` with boundary |

---

## Type Mapping

The frontend and backend maintain corresponding type definitions for API data. **Note:** The `/process` endpoint returns `DetailedResponse`, not `ProcessingResponse`. `ProcessingResponse` is an internal dataclass used for caching.

### Standard Response DTOs

| Backend (Python) | Endpoint | Frontend (TypeScript) | Purpose |
|------------------|----------|----------------------|---------|
| `ApiEnvelope[T]` (Generic Pydantic model) | New endpoints (recommended) | `ApiEnvelope<T>` (interface) | Standard response envelope with status, data, meta, links, timestamp |
| `ProcessApiResponse` (Pydantic model) | `/api/v2/process` | `ProcessApiResponse` (interface) | Transaction processing result with aggregated data and metadata |
| `ResultsApiResponse` (Pydantic model) | `/api/v2/results/<id>` | `ResultsApiResponse` (interface) | Cached results with accounts data and drilldown URLs |
| `RecalculateApiResponse` (Pydantic model) | `/api/v2/recalculate-statistics` | `RecalculateApiResponse` (interface) | Statistical recalculation result with updated highlights |
| `CategoryMonthsApiResponse` (Pydantic model) | `/api/v2/results/.../categories/.../months` | `CategoryMonthsApiResponse` (interface) | Category-by-month drilldown data |
| `MonthCategoriesApiResponse` (Pydantic model) | `/api/v2/results/.../months/.../categories` | `MonthCategoriesApiResponse` (interface) | Month-by-category drilldown data |
| `CategoryMonthTransactionsApiResponse` (Pydantic model) | `/api/v2/results/.../transactions` | `CategoryMonthTransactionsApiResponse` (interface) | Individual transaction details |
| `ErrorApiResponse` (Pydantic model) | All endpoints (errors) | `ErrorApiResponse` (interface) | Standard error response format |

### Low-Level Types

| Backend (Python) | Frontend (TypeScript) | Purpose |
|------------------|----------------------|---------|
| `dict` (Python dict) | `Record<string, T>` | Generic object type |
| `List[Dict[str, Any]]` | `Array<{...}>` | Array of objects |
| Flask `Response` object | `Promise<T>` | HTTP response wrapper |
| Pydantic model | TypeScript interface | Data validation and typing |
| `Optional[str]` | `string \| null \| undefined` | Optional string field |
| `List[str]` | `string[]` | String array |
| `Dict[str, List[str]]` | `Record<string, string[]>` | Object with string array values |

---

## Contract Summary

The **API contract** between frontend and backend is explicitly defined by:

### 1. **URL Paths**
- `/api/v2/process` - Process CSV transactions
- `/api/v2/results/<result_id>` - Retrieve processed results
- `/api/v2/results/<r>/accounts/<a>/categories/<c>/months` - Category months drilldown
- `/api/v2/results/<r>/accounts/<a>/months/<m>/categories` - Month categories drilldown
- `/api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions` - Cell transactions drilldown
- `/api/v2/recalculate-statistics` - Recalculate statistical highlights

### 2. **HTTP Methods**
- **POST**: Mutations (process, recalculate)
- **GET**: Retrieval (results, drilldown)

### 3. **Content Types**
- `multipart/form-data`: File uploads (CSV, config)
- `application/json`: Data payloads (statistics recalculation)

### 4. **Response Formats**

**Important:** Response structures vary by endpoint. Each endpoint returns a format optimized for its specific use case.

| Endpoint | HTTP Method | Response Structure |
|----------|-------------|-------------------|
| `/api/v2/process` | POST | `{data: AggregatedRow[], metadata: {result_id, row_count, processing_time, ml_enabled, date_range}}` |
| `/api/v2/results/<result_id>` | GET | `{result_id, accounts_data: {accounts: AccountData[], highlights: Highlights}, drilldown_urls_by_account: {account_id: DrilldownUrls}}` |
| `/api/v2/results/<r>/accounts/<a>/categories/<c>/months` | GET | `{result_id, account_id, account_name, category_id, category_name, data: MonthData[], highlights?: {row_id: string[]}}` |
| `/api/v2/results/<r>/accounts/<a>/months/<m>/categories` | GET | `{result_id, account_id, account_name, month_id, month_name, data: CategoryData[], highlights?: {row_id: string[]}}` |
| `/api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions` | GET | `{result_id, account_id, account_name, category_id, category_name, month_id, month_name, data: TransactionDetail[], highlights?: {row_id: string[]}}` |
| `/api/v2/recalculate-statistics` | POST | `{status: 'success', result_id, highlights: {row_id: string[]}, algorithms: string[], direction: 'columns'|'rows'}` |

**Error Response Format:**
```json
{
  "code": 400,
  "message": "Human-readable error description",
  "details": { ... }  // optional, additional context
}
```

### 5. **Status Codes**
- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Data validation failed
- `500 Internal Server Error`: Server-side failure

### 6. **Standard Response Envelope (for New Endpoints)**

For consistency across new API endpoints, use the **standard response envelope** format:

```json
{
  "status": "success",
  "data": { ... },           // Endpoint-specific payload
  "meta": {
    "request_id": "...",
    "version": "v2",
    "api_version": "2.0"
  },
  "links": {
    "self": "/api/v2/endpoint",
    "doc": "/docs/api/v2/endpoint"
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

**Backend Implementation:**
```python
from whatsthedamage.models.api_responses import ApiEnvelope

@v2_bp.route('/new-endpoint', methods=['GET'])
def new_endpoint():
    payload = SomeDataModel(...)
    return ApiEnvelope[SomeDataModel](
        status='success',
        data=payload,
        meta={'request_id': 'req_123', 'version': 'v2'},
        links={'self': '/api/v2/new-endpoint'}
    )
```

**Frontend Implementation:**
```typescript
import { ApiEnvelope, fetchWithEnvelope, fetchEnvelope } from '../js/api';

// Get just the data (unwrapped)
const data = await fetchWithEnvelope<MyData>('/api/v2/new-endpoint');

// Get full envelope with metadata and links
const envelope = await fetchEnvelope<MyData>('/api/v2/new-endpoint');
```

**Notes:**
- Existing endpoints maintain their specific response formats for compatibility
- New endpoints **should** use the envelope for consistency
- The envelope provides standardized metadata, hypermedia links, and timestamp
- Error responses use the same envelope with `status: 'error'`

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            FRONTEND                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Vue Components                               │  │
│  │  Index.vue │ Results.vue │ CategoryMonthsList.vue │ ...           │  │
│  └───────────────────────────────┬─────────────────────────────────┘  │
│                                  │                                    │
│                                  ▼                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Pinia Stores                                 │  │
│  │  useFormStore │ useLocaleStore │ useFeedbackStore │ ...          │  │
│  └───────────────────────────────┬─────────────────────────────────┘  │
│                                  │                                    │
│                                  ▼                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              frontend/src/js/api.ts                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │  │
│  │  │ fetchApi         │  │ fetchResults     │  │ processTrans-  │ │  │
│  │  │ fetchWithError   │  │ fetchCategory    │  │ actions        │ │  │
│  │  │ postData         │  │ Months           │  │                │ │  │
│  │  │ getApiUrl        │  │ fetchMonthCate-  │  │                │ │  │
│  │  └─────────────────┘  │ gories           │  │                │ │  │
│  │                     │  │ fetchCategory-   │  │                │ │  │
│  │                     │  │ MonthTransactions│  │                │ │  │
│  │                     │  │ recalculate-    │  │                │ │  │
│  │                     │  │ Statistics      │  │                │ │  │
│  │                     └─────────────────────────────────────────┘│  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │         HTTP / HTTPS            │
                    │  POST /api/v2/process            │
                    │  GET  /api/v2/results/{id}       │
                    │  GET  /api/v2/.../drilldown      │
                    │  POST /api/v2/recalculate       │
                    └─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            BACKEND                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              src/whatsthedamage/api/v2/endpoints.py             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │  │
│  │  │ process_         │  │ get_results      │  │ get_category-  │ │  │
│  │  │ transactions    │  │                 │  │ months         │ │  │
│  │  │ get_month_       │  │                 │  │ get_month-     │ │  │
│  │  │ categories      │  │                 │  │ categories     │ │  │
│  │  │ get_category_    │  │                 │  │ get_category-  │ │  │
│  │  │ month_           │  │                 │  │ month_         │ │  │
│  │  │ transactions    │  │                 │  │ transactions   │ │  │
│  │  │ recalculate_    │  │                 │  │                │ │  │
│  │  │ statistics      │  │                 │  │                │ │  │
│  │  └─────────────────┘  └─────────────────┘  └────────────────┘ │  │
│  └───────────────────────────┬─────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                                │  │
│  │  ProcessingService │ CacheService │ StatisticalService       │  │
│  │  ResponseBuilderService │ DrilldownResponseService            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Data Layer                                   │  │
│  │  Models │ Database │ File System │ ML Models                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**`frontend/src/js/api.ts`** implements the **client side** of the API contract with:
- Type-safe request/response handling
- Comprehensive error management
- Clean abstraction for Vue components

**`backend/src/whatsthedamage/api/v2/endpoints.py`** implements the **server side** of the API contract with:
- Route definitions and HTTP method binding
- Service delegation for business logic
- Consistent response formatting

Together they form a **clean API-first architecture** where both layers can evolve independently as long as the contract (URLs, methods, data formats, status codes) remains stable.

---

## Best Practices

### For Frontend Developers

1. **Always use `api.ts` functions** for API communication - never call `fetch` directly
2. **Handle errors** at the component level using `AppError` information
3. **Use TypeScript types** from `types/api.ts` for response data
4. **For new endpoints**: Add function to `api.ts`, corresponding type to `types/api.ts`, and tests
5. **For multipart uploads**: Use `FormData` and the `processTransactions` pattern (bypasses `fetchApi` due to Content-Type restrictions)
6. **API Base URL Configuration**: The frontend uses `VITE_API_BASE_URL` environment variable (defaults to `/api/v2`) to enable **standalone frontend deployment** targeting any backend URL

### For Backend Developers

1. **Keep routes thin** - delegate business logic to services
2. **Use service factory functions** (`_get_*_service()`) for dependency injection
3. **Return consistent JSON** with proper HTTP status codes
4. **Validate all inputs** at the route level
5. **Cache results** for drilldown navigation using `CacheService`

### For Both

1. **Maintain the contract** - changes to one side may require changes to the other
2. **Version the API** - use `/api/v2/` prefix for breaking changes
3. **Document endpoints** - keep docstrings and JSDoc comments up to date
4. **Test the integration** - ensure frontend and backend work together

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2 | 2025-01 | Initial API-first architecture with detailed drilldown endpoints |
