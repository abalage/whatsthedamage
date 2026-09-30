# REST API Documentation

The REST API provides programmatic access to bank transaction CSV processing with detailed JSON responses. API v2 supports regex-based and ML-based categorization, multi-account handling, transaction persistence, corrections, and aggregation-based drilldown navigation.

All data endpoints require authentication. Every transaction, processing result, and correction is scoped to the authenticated user.

## Base URL

```
http://localhost:5000/api/v2
```

All endpoints are under the `/api/v2` path.

## Table of Contents

- [Authentication Endpoints](#authentication-endpoints)
- [Processing Results Endpoints](#processing-results-endpoints)
- [Transaction Endpoints](#transaction-endpoints)
- [Transaction Aggregation](#transaction-aggregation)
- [Correction Endpoints](#correction-endpoints)
- [Category Endpoints](#category-endpoints)
- [CSV Profile Endpoints](#csv-profile-endpoints)
- [Statistical Endpoints](#statistical-endpoints)
- [Request Parameters](#request-parameters)
- [Response Formats](#response-formats)
- [Error Responses](#error-responses)
- [HTTP Status Codes](#http-status-codes)
- [OpenAPI Specification](#openapi-specification)
- [Security Considerations](#security-considerations)
- [Endpoint Summary](#endpoint-summary)

---

## Authentication Endpoints

Authentication uses session cookies. A successful register or login sets an opaque `session_token` cookie (HttpOnly, Secure, SameSite=Strict) backed by a database session. State-changing requests (POST, PUT, DELETE on protected endpoints) must additionally send the `X-CSRF-Token` header.

### Register

Create a new user account. Registration generates a one-time recovery code and creates an initial session.

**Endpoint:**
```
POST /api/v2/auth/register
```

**Content-Type:** `application/json`

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `username` | Yes | string | Username |
| `password` | Yes | string | Password (strength requirements enforced) |

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "correct-horse-battery-staple"}'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "created_at": "2026-09-29T10:00:00"
  },
  "recovery_code": "XXXX-XXXX-XXXX",
  "csrf_token": "eyJhbGciOi...",
  "session_expires_at": "2026-09-29T18:00:00"
}
```

The `recovery_code` is displayed only once. It cannot be retrieved later and must be saved by the user.

**Status Codes:**
- `201` - Successfully registered
- `400` - Validation error (missing fields, invalid input)
- `409` - Username already exists
- `422` - Password too weak

---

### Login

Authenticate a user and create a session.

**Endpoint:**
```
POST /api/v2/auth/login
```

**Content-Type:** `application/json`

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `username` | Yes | string | Username |
| `password` | Yes | string | Password |
| `remember_me` | No | boolean | Extend the session lifetime (default: `false`) |

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "correct-horse-battery-staple"}'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "last_login_at": "2026-09-28T09:00:00"
  },
  "csrf_token": "eyJhbGciOi...",
  "session_expires_at": "2026-09-29T18:00:00"
}
```

**Status Codes:**
- `200` - Successfully logged in
- `400` - Validation error (missing fields)
- `401` - Invalid credentials
- `429` - Too many login attempts (rate limited)

Login is rate limited to 5 attempts per 15 minutes per username and IP combination. When the limit is exceeded, the response includes a `Retry-After` header.

---

### Logout

Revoke the current session and clear the session cookie. Requires authentication and the `X-CSRF-Token` header.

**Endpoint:**
```
POST /api/v2/auth/logout
```

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/v2/auth/logout \
  -H "X-CSRF-Token: eyJhbGciOi..."
```

**Response:**
```json
{"message": "Successfully logged out"}
```

**Status Codes:**
- `200` - Successfully logged out
- `401` - Not authenticated
- `403` - Invalid or missing CSRF token

---

### Get Current User

Return information about the authenticated user. Includes a CSRF token only when the current session does not have one yet; repeat calls do not rotate an existing token.

**Endpoint:**
```
GET /api/v2/auth/me
```

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/auth/me
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "created_at": "2026-09-01T10:00:00",
    "last_login_at": "2026-09-29T09:00:00",
    "is_active": true,
    "opt_in_sharing": false
  },
  "csrf_token": "eyJhbGciOi..."
}
```

**Status Codes:**
- `200` - Success
- `401` - Not authenticated

---

### Reset Password

Reset the password using the one-time recovery code issued during registration (or a previous reset). Public endpoint; no session or CSRF token required. All existing sessions are invalidated on success and a new recovery code is issued.

**Endpoint:**
```
POST /api/v2/auth/reset-password
```

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `username` | Yes | string | Username |
| `recovery_code` | Yes | string | One-time recovery code |
| `new_password` | Yes | string | New password (strength requirements enforced) |

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/v2/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "recovery_code": "XXXX-XXXX-XXXX", "new_password": "new-correct-horse"}'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "created_at": "2026-09-01T10:00:00",
    "last_login_at": null,
    "is_active": true,
    "opt_in_sharing": false
  },
  "new_recovery_code": "YYYY-YYYY-YYYY"
}
```

**Status Codes:**
- `200` - Password successfully reset
- `400` - Validation error (missing fields, invalid input)
- `401` - Invalid username or recovery code
- `422` - Password too weak
- `429` - Too many attempts (rate limited to 5 per 15 minutes per IP)

---

### Get CSRF Token

Mint a CSRF token for the current session. Send it in the `X-CSRF-Token` header on state-changing requests.

**Endpoint:**
```
GET /api/v2/auth/csrf-token
```

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/auth/csrf-token
```

**Response:**
```json
{"csrf_token": "eyJhbGciOi..."}
```

**Status Codes:**
- `200` - CSRF token generated
- `401` - Not authenticated

---

## Processing Results Endpoints

### Process CSV File

Upload a CSV file, process and persist its transactions for the authenticated user, and create a processing result. Returns metadata only; transaction data is fetched via the `/transactions` endpoint.

**Endpoint:**
```
POST /api/v2/processing-results
```

**Method:** `POST`

**Content-Type:** `multipart/form-data`

**Requires:** session cookie and `X-CSRF-Token` header

**Curl Examples:**
```bash
# Basic usage
curl -X POST http://localhost:5000/api/v2/processing-results \
  -H "X-CSRF-Token: eyJhbGciOi..." \
  -F "csv_file=@transactions.csv"

# With date filtering
curl -X POST http://localhost:5000/api/v2/processing-results \
  -H "X-CSRF-Token: eyJhbGciOi..." \
  -F "csv_file=@transactions.csv" \
  -F "start_date=2024.01.01" \
  -F "end_date=2024.12.31"

# With custom config and ML categorization
curl -X POST http://localhost:5000/api/v2/processing-results \
  -H "X-CSRF-Token: eyJhbGciOi..." \
  -F "csv_file=@transactions.csv" \
  -F "config_file=@config.yml" \
  -F "ml_enabled=true"

# With CSV profile selection
curl -X POST http://localhost:5000/api/v2/processing-results \
  -H "X-CSRF-Token: eyJhbGciOi..." \
  -F "csv_file=@transactions.csv" \
  -F "csv_profile_id=otp-hu"
```

**Status Codes:**
- `201` - Processing result created
- `400` - Bad request (missing file, invalid parameters)
- `401` - Not authenticated
- `409` - Conflict (duplicate transaction)
- `422` - Unprocessable entity (CSV parsing error, validation failed)
- `500` - Internal server error

---

### List Processing Results

List the authenticated user's processing results with pagination.

**Endpoint:**
```
GET /api/v2/processing-results
```

**Query Parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `limit` | No | integer | `100` | Maximum number of results to return |
| `offset` | No | integer | `0` | Pagination offset |

**Curl Example:**
```bash
curl -X GET "http://localhost:5000/api/v2/processing-results?limit=20&offset=0"
```

**Status Codes:**
- `200` - Successfully retrieved processing results
- `401` - Not authenticated
- `500` - Internal server error

---

### Get Processing Result Metadata

Get metadata for a specific processing result. Returns metadata only; use the `/transactions` endpoint with the `result_id` filter to fetch the transaction data.

**Endpoint:**
```
GET /api/v2/processing-results/<result_id>
```

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the processing result |

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/processing-results/550e8400-e29b-41d4-a716-446655440000
```

**Status Codes:**
- `200` - Successfully retrieved metadata
- `401` - Not authenticated
- `403` - Result belongs to another user
- `404` - Processing result not found
- `500` - Internal server error

---

## Transaction Endpoints

Transactions are persisted entities scoped to the authenticated user. The `result_id` query parameter optionally filters any transaction view to a single processing result; when omitted, all of the user's transactions are shown.

### List Transactions

**Endpoint:**
```
GET /api/v2/transactions
```

**Query Parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `limit` | No | integer | `100` | Maximum number of transactions to return |
| `offset` | No | integer | `0` | Pagination offset |
| `start_date` | No | string | - | Filter by start date (`YYYY-MM-DD`) |
| `end_date` | No | string | - | Filter by end date (`YYYY-MM-DD`) |
| `category_id` | No | string | - | Filter by category ID |
| `account` | No | string | - | Filter by account |
| `partner` | No | string | - | Filter by partner name (searches `original_partner` and `partner`) |
| `transaction_type` | No | string | - | Filter by transaction type (`debit`/`credit`) |
| `month` | No | string | - | Filter by month (`YYYY-MM`) |
| `min_amount` | No | number | - | Filter by minimum amount |
| `max_amount` | No | number | - | Filter by maximum amount |
| `result_id` | No | string | - | Filter by processing result |
| `sort_by` | No | string | `date` | Sort field: `date`, `amount`, `partner`, `account`, `category` |
| `sort_order` | No | string | `desc` | Sort order: `asc` or `desc` |

**Curl Example:**
```bash
curl -X GET "http://localhost:5000/api/v2/transactions?limit=50&month=2026-09&sort_by=amount"
```

**Status Codes:**
- `200` - Successfully retrieved transactions
- `400` - Invalid query parameters
- `401` - Not authenticated
- `500` - Internal server error

---

### Create Transaction

Create a single transaction entity. Duplicate transactions (same account, date, partner, amount) are rejected with `409`.

**Endpoint:**
```
POST /api/v2/transactions
```

**Content-Type:** `application/json`

**Requires:** session cookie and `X-CSRF-Token` header

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `date` | Yes | string | Transaction date (`YYYY-MM-DD`) |
| `transaction_type` | Yes | string | Transaction type (`debit`/`credit`) |
| `original_partner` | Yes | string | Original partner name from the CSV |
| `amount` | Yes | number | Transaction amount |
| `currency` | Yes | string | Currency code |
| `account` | Yes | string | Account identifier |
| `category_id` | No | string | Assigned category identifier |
| `partner` | No | string | Corrected partner name |
| `notice` | No | string | Transaction notice/comment |
| `confidence` | No | number | Categorization confidence score |

**Status Codes:**
- `201` - Successfully created transaction
- `400` - Bad request (missing required fields, invalid data)
- `401` - Not authenticated
- `409` - Conflict (duplicate transaction)
- `500` - Internal server error

---

### Get Transaction

Retrieve a single transaction by ID.

**Endpoint:**
```
GET /api/v2/transactions/<transaction_id>
```

**Status Codes:**
- `200` - Successfully retrieved transaction
- `401` - Not authenticated
- `403` - Transaction belongs to another user
- `404` - Transaction not found
- `500` - Internal server error

---

### Update Transaction

Update the non-deduplication fields of a transaction (`category_id`, `partner`, `notice`, `confidence`). Updating these fields automatically creates or updates a correction entry for the `original_partner`, so future uploads with the same merchant receive the same correction.

**Endpoint:**
```
PUT /api/v2/transactions/<transaction_id>
```

**Content-Type:** `application/json`

**Requires:** session cookie and `X-CSRF-Token` header

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `category_id` | No | string | New category identifier |
| `partner` | No | string | New corrected partner name |
| `notice` | No | string | New transaction notice/comment |
| `confidence` | No | number | New confidence score |

**Status Codes:**
- `200` - Successfully updated transaction
- `400` - Bad request (invalid data)
- `401` - Not authenticated
- `403` - Transaction belongs to another user
- `404` - Transaction not found
- `500` - Internal server error

---

### Delete Transaction

Delete a transaction owned by the authenticated user.

**Endpoint:**
```
DELETE /api/v2/transactions/<transaction_id>
```

**Requires:** session cookie and `X-CSRF-Token` header

**Response:**
```json
{"message": "Transaction deleted successfully"}
```

**Status Codes:**
- `200` - Successfully deleted transaction
- `401` - Not authenticated
- `403` - Transaction belongs to another user
- `404` - Transaction not found
- `500` - Internal server error

---

## Transaction Aggregation

### Aggregate Transactions

Group the authenticated user's transactions for drilldown views, with statistical highlights computed over the parent month x category matrix scope. This endpoint replaces the removed per-processing-result drilldown endpoints (`/results/.../accounts/.../...`).

**Endpoint:**
```
GET /api/v2/transactions/aggregate
```

**Query Parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `group_by` | Yes | string | - | Grouping dimension: `category`, `month`, `account`, or `category_month` |
| `result_id` | No | string | - | Filter by processing result |
| `account` | No | string | - | Filter by account |
| `category_id` | No | string | - | Filter by category |
| `month` | No | string | - | Filter by month (`YYYY-MM`) |
| `algorithms` | No | string | `iqr,pareto` | Comma-separated algorithm names |
| `direction` | No | string | `columns` | Analysis direction: `columns` or `rows` |

**Curl Examples:**
```bash
# Month-by-month aggregation for a category within an account
curl -X GET "http://localhost:5000/api/v2/transactions/aggregate?group_by=month&category_id=grocery&account=account_1"

# Category-by-category aggregation for a specific month
curl -X GET "http://localhost:5000/api/v2/transactions/aggregate?group_by=category&month=2026-09"

# Category x month matrix cells
curl -X GET "http://localhost:5000/api/v2/transactions/aggregate?group_by=category_month"
```

**Response:**
```json
{
  "result_id": null,
  "account": "account_1",
  "category_id": "grocery",
  "month": null,
  "group_by": "month",
  "groups": {
    "2026-08": ["..."],
    "2026-09": ["..."]
  },
  "highlights": {
    "2026-08": ["outlier"],
    "2026-09": []
  },
  "total_count": 145
}
```

`groups` maps group keys to arrays of transaction objects (see [Transaction Object](#transaction-object)). Group keys depend on `group_by`: months as `YYYY-MM`, category IDs, account names, or `{category}_{YYYY-MM}` for `category_month`. `highlights` maps the same group keys to statistical highlight types computed over the parent matrix scope.

**Status Codes:**
- `200` - Successfully retrieved aggregated data
- `400` - Invalid parameters (missing or invalid `group_by`, invalid `direction`)
- `401` - Not authenticated
- `500` - Internal server error

---

## Correction Endpoints

Corrections store per-user overrides for transaction metadata by original partner name. They are applied automatically on future CSV uploads and when updating transactions.

### List Corrections

**Endpoint:**
```
GET /api/v2/corrections
```

**Query Parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `limit` | No | integer | `100` | Maximum number of corrections to return |
| `offset` | No | integer | `0` | Pagination offset |
| `original_partner` | No | string | - | Filter by original partner name |

**Status Codes:**
- `200` - Successfully retrieved corrections
- `401` - Not authenticated
- `500` - Internal server error

---

### Create Correction

**Endpoint:**
```
POST /api/v2/corrections
```

**Content-Type:** `application/json`

**Requires:** session cookie and `X-CSRF-Token` header

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `original_partner` | Yes | string | Original partner name to correct |
| `corrected_partner` | No | string | Corrected partner name |
| `corrected_category_id` | No | string | Corrected category ID |
| `corrected_notice` | No | string | Corrected notice |

**Status Codes:**
- `201` - Successfully created correction
- `400` - Bad request (missing required fields, invalid data)
- `401` - Not authenticated
- `409` - Correction already exists
- `500` - Internal server error

---

### Get Correction

**Endpoint:**
```
GET /api/v2/corrections/<correction_id>
```

**Status Codes:**
- `200` - Successfully retrieved correction
- `401` - Not authenticated
- `403` - Correction belongs to another user
- `404` - Correction not found
- `500` - Internal server error

---

### Update Correction

**Endpoint:**
```
PUT /api/v2/corrections/<correction_id>
```

**Content-Type:** `application/json`

**Requires:** session cookie and `X-CSRF-Token` header

**Request Body:** any of `corrected_partner`, `corrected_category_id`, `corrected_notice`.

**Status Codes:**
- `200` - Successfully updated correction
- `400` - Bad request (no valid fields to update)
- `401` - Not authenticated
- `403` - Correction belongs to another user
- `404` - Correction not found
- `500` - Internal server error

---

### Delete Correction

**Endpoint:**
```
DELETE /api/v2/corrections/<correction_id>
```

**Requires:** session cookie and `X-CSRF-Token` header

**Response:**
```json
{"message": "Correction deleted successfully"}
```

**Status Codes:**
- `200` - Successfully deleted correction
- `401` - Not authenticated
- `403` - Correction belongs to another user
- `404` - Correction not found
- `500` - Internal server error

---

## Category Endpoints

### Get All Categories

Retrieve all available category definitions for transaction categorization.

**Endpoint:**
```
GET /api/v2/categories
```

**Description:**
Returns the full list of CategoryDefinition objects. Each category has an `id` field (for API usage) and a `default_name` field (for display, can be localized).

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/categories
```

**Response:**
```json
[
  {
    "id": "grocery",
    "default_name": "Grocery",
    "patterns": ["tesco", "aldi", "lidl", "spar"]
  },
  {
    "id": "clothes",
    "default_name": "Clothing",
    "patterns": ["h&m", "zara", "c&a"]
  }
]
```

**Status Codes:**
- `200` - Successfully retrieved category definitions

---

### Get Cost of Living Categories

Retrieve categories that are counted in cost of living calculations.

**Endpoint:**
```
GET /api/v2/categories/cost-of-living
```

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/categories/cost-of-living
```

**Status Codes:**
- `200` - Successfully retrieved list of categories

---

## CSV Profile Endpoints

CSV profiles define the format and parsing rules for different bank CSV export formats.

### List All CSV Profiles

**Endpoint:**
```
GET /api/v2/csv-profiles
```

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/csv-profiles
```

**Response:**
```json
[
  {
    "id": "otp-hu",
    "name": "OTP Bank (Hungary)",
    "description": "CSV export format for OTP Bank Hungary",
    "version": "1.0",
    "csv_config": {
      "dialect": "excel",
      "delimiter": ";",
      "date_attribute_format": "%Y.%m.%d"
    }
  }
]
```

**Status Codes:**
- `200` - Successfully retrieved CSV profiles
- `500` - Failed to retrieve CSV profiles

---

### Get Specific CSV Profile

**Endpoint:**
```
GET /api/v2/csv-profiles/<profile_id>
```

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `profile_id` | Yes | string | The unique identifier of the CSV profile (e.g., `otp-hu`) |

**Curl Example:**
```bash
curl -X GET http://localhost:5000/api/v2/csv-profiles/otp-hu
```

**Status Codes:**
- `200` - Successfully retrieved CSV profile
- `404` - CSV profile not found

---

## Statistical Endpoints

### Recalculate Statistics

Recalculate statistical highlights from persisted transactions using specified algorithms and analysis direction.

**Endpoint:**
```
POST /api/v2/recalculate-statistics
```

**Content-Type:** `application/json`

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `result_id` | No | string | UUID of a processing result to scope to. Omitted = all of the user's transactions. |
| `algorithms` | Yes | array[string] | List of algorithm names (e.g., `["iqr", "pareto"]`) |
| `direction` | Yes | string | Analysis direction: `rows` or `columns` |

**Curl Examples:**
```bash
# All transactions, IQR and Pareto, column-based analysis
curl -X POST http://localhost:5000/api/v2/recalculate-statistics \
  -H "Content-Type: application/json" \
  -d '{"algorithms": ["iqr", "pareto"], "direction": "columns"}'

# Scoped to one processing result, row-based, IQR only
curl -X POST http://localhost:5000/api/v2/recalculate-statistics \
  -H "Content-Type: application/json" \
  -d '{"result_id": "550e8400-e29b-41d4-a716-446655440000", "algorithms": ["iqr"], "direction": "rows"}'
```

**Response:**
```json
{
  "status": "success",
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "highlights": {
    "account_1|2026-09|grocery": ["outlier", "pareto"]
  },
  "algorithms": ["iqr", "pareto"],
  "direction": "columns"
}
```

Highlights are keyed by matrix-view cell ID: `{account}|{month}|{category}` (month as `YYYY-MM`, category as `category_id` or `uncategorized`).

**Status Codes:**
- `200` - Successfully recalculated statistics
- `400` - Bad request (missing parameters, invalid values)
- `401` - Not authenticated
- `404` - Processing result not found
- `500` - Internal server error

---

## Request Parameters

### Processing Endpoint Parameters (`POST /api/v2/processing-results`)

All parameters are submitted as `multipart/form-data`.

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `csv_file` | Yes | file | - | CSV file containing bank transactions. Required. |
| `config_file` | No | file | - | Optional YAML configuration file. Uses default config if not provided. |
| `start_date` | No | string | - | Filter start date. Format matches the profile's `date_attribute_format` (default: `%Y.%m.%d`). Example: `2024.01.01` |
| `end_date` | No | string | - | Filter end date. Format matches the profile's `date_attribute_format`. Example: `2024.12.31` |
| `date_format` | No | string | From profile | Date format string (Python strptime format). Overrides the profile default. Example: `%Y-%m-%d` |
| `ml_enabled` | No | boolean | `false` | Enable ML-based categorization instead of regex patterns. Accepts `true` or `false` as string. |
| `category_filter` | No | string | - | Filter results to a specific category by `category_id` (e.g., `grocery`). Use `/api/v2/categories` to see available IDs. |
| `csv_profile_id` | No | string | Default profile | CSV profile ID to use for parsing (e.g., `otp-hu`). Uses the default profile if not provided. |

---

## Response Formats

### Processing Result Created (`POST /api/v2/processing-results`)

Returns processing metadata only; the transactions themselves are persisted and fetched via `/api/v2/transactions?result_id=<result_id>`.

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "csv_profile_id": "otp-hu",
  "row_count": 145,
  "processing_time": 0.456,
  "ml_enabled": false,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "created_at": "2026-09-29T10:00:00",
  "transactions_count": 145,
  "message": "Processing result created successfully"
}
```

### Processing Result Metadata (`GET /api/v2/processing-results/<result_id>`)

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "csv_profile_id": "otp-hu",
  "row_count": 145,
  "processing_time": 0.456,
  "ml_enabled": false,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "created_at": "2026-09-29T10:00:00",
  "transactions_url": "/api/v2/transactions?result_id=550e8400-e29b-41d4-a716-446655440000"
}
```

### Transaction Object

```json
{
  "id": 1,
  "user_id": 1,
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2026-09-15T00:00:00",
  "transaction_type": "debit",
  "original_partner": "TESCO",
  "amount": -12500.0,
  "currency": "HUF",
  "account": "12345678-12345678",
  "deduplication_hash": "a3f5...",
  "category_id": "grocery",
  "partner": "Tesco",
  "notice": "Weekly shopping",
  "confidence": 0.95,
  "created_at": "2026-09-29T10:00:00",
  "updated_at": "2026-09-29T10:00:00"
}
```

Dates are stored as datetime values and serialized as ISO 8601 strings; months are addressed as `YYYY-MM` in filters and aggregate keys.

### Transactions List (`GET /api/v2/transactions`)

```json
{
  "transactions": ["..."],
  "total_count": 145,
  "limit": 100,
  "offset": 0
}
```

`transactions` is an array of [Transaction Objects](#transaction-object).

### Corrections List (`GET /api/v2/corrections`)

```json
{
  "corrections": [
    {
      "id": 1,
      "user_id": 1,
      "original_partner": "TESCO",
      "corrected_partner": "Tesco",
      "corrected_category_id": "grocery",
      "corrected_notice": null,
      "created_at": "2026-09-29T10:00:00",
      "updated_at": "2026-09-29T10:00:00"
    }
  ],
  "total_count": 1,
  "limit": 100,
  "offset": 0
}
```

---

## Error Responses

Error responses follow the standardized `ErrorResponse` format emitted by the centralized error handlers:

```json
{
  "code": 404,
  "message": "Result not found or does not belong to you",
  "details": {"error": "Result ID 550e8400-... not found"}
}
```

**Field Descriptions:**

- `code`: HTTP status code (integer)
- `message`: Human-readable error description
- `details`: Additional error context (optional, may be absent)

Note: some endpoint handlers currently return a simplified `{"error": "<message>"}` body instead of the standardized format. Treat the HTTP status code as authoritative and prefer the standardized format for new integrations.

---

## HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | Success | Request processed successfully |
| `201` | Created | Resource created (register, processing result, transaction, correction) |
| `400` | Bad Request | Missing required file, invalid parameters, validation error |
| `401` | Unauthorized | Not authenticated, invalid credentials, invalid session |
| `403` | Forbidden | Resource belongs to another user, invalid or missing CSRF token |
| `404` | Not Found | Transaction, correction, result, or CSV profile not found |
| `409` | Conflict | Duplicate transaction or correction |
| `422` | Unprocessable Entity | CSV parsing error, invalid date format, password too weak |
| `429` | Too Many Requests | Rate limit exceeded (login, password reset) |
| `500` | Internal Server Error | Server-side processing error |

---

## OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available for programmatic access and documentation generation.

**Endpoint:**
```
GET /api/v2/openapi.json
```

**Description:**
Returns the full OpenAPI specification in JSON format, including all endpoints, parameters, security schemes, and response schemas. This can be used with OpenAPI-compatible tools for documentation generation, client code generation, or testing.

**Curl Example:**
```bash
# Download the OpenAPI specification
curl -X GET http://localhost:5000/api/v2/openapi.json -o openapi.json

# View in browser
open http://localhost:5000/api/v2/openapi.json
```

**Status Codes:**
- `200` - Successfully returned OpenAPI specification

---

## Security Considerations

**Current state:**
- Session-cookie authentication (HttpOnly, Secure, SameSite=Strict cookies backed by database sessions)
- CSRF token verification on all state-changing requests (`X-CSRF-Token` header)
- Per-user data isolation: transactions, results, and corrections are scoped to the authenticated user
- Rate limiting on sensitive endpoints (login, registration, password reset)
- Passwords hashed with Argon2
- Input validation (file types, MIME types, parameter validation)
- Secure filename handling (prevents path traversal)
- CSV file validation (structure, required columns)
- Date format and range validation
- CORS enabled for development (`http://localhost:3000`, `http://127.0.0.1:3000`)
- Production CORS configurable via Flask-CORS

**Recommendations for Production:**
- Configure CORS origins appropriately for your frontend domain
- Use HTTPS in production
- Back up the database (users, sessions, and transactions are persisted)
- Protect the database file from direct download by the web server

---

## Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/auth/register` | Register a new user account |
| `POST` | `/api/v2/auth/login` | Authenticate and create a session |
| `POST` | `/api/v2/auth/logout` | Revoke the current session |
| `GET` | `/api/v2/auth/me` | Get current user information |
| `POST` | `/api/v2/auth/reset-password` | Reset password using a recovery code |
| `GET` | `/api/v2/auth/csrf-token` | Get a new CSRF token |
| `POST` | `/api/v2/processing-results` | Process and import a CSV file |
| `GET` | `/api/v2/processing-results` | List processing results |
| `GET` | `/api/v2/processing-results/<result_id>` | Get processing result metadata |
| `GET` | `/api/v2/transactions` | List transactions (paginated, filterable) |
| `POST` | `/api/v2/transactions` | Create a transaction |
| `GET` | `/api/v2/transactions/<transaction_id>` | Get a transaction |
| `PUT` | `/api/v2/transactions/<transaction_id>` | Update a transaction |
| `DELETE` | `/api/v2/transactions/<transaction_id>` | Delete a transaction |
| `GET` | `/api/v2/transactions/aggregate` | Aggregate transactions for drilldown views |
| `GET` | `/api/v2/corrections` | List corrections |
| `POST` | `/api/v2/corrections` | Create a correction |
| `GET` | `/api/v2/corrections/<correction_id>` | Get a correction |
| `PUT` | `/api/v2/corrections/<correction_id>` | Update a correction |
| `DELETE` | `/api/v2/corrections/<correction_id>` | Delete a correction |
| `POST` | `/api/v2/recalculate-statistics` | Recalculate statistics with custom settings |
| `GET` | `/api/v2/categories` | Get all category definitions |
| `GET` | `/api/v2/categories/cost-of-living` | Get cost of living categories |
| `GET` | `/api/v2/csv-profiles` | List all CSV profiles |
| `GET` | `/api/v2/csv-profiles/<profile_id>` | Get specific CSV profile |
| `GET` | `/api/v2/openapi.json` | Get OpenAPI specification |
