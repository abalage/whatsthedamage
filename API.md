# REST API Documentation

The REST API provides programmatic access to bank transaction CSV processing with detailed JSON responses. API v2 supports regex-based and ML-based categorization, multi-account handling, and drilldown navigation.

## Base URL

```
http://localhost:5000/api/v2
```

All endpoints are under the `/api/v2` path.

## Table of Contents

- [Processing Endpoints](#processing-endpoints)
- [Results Endpoints](#results-endpoints)
- [Drilldown Endpoints](#drilldown-endpoints)
- [Category Endpoints](#category-endpoints)
- [CSV Profile Endpoints](#csv-profile-endpoints)
- [Statistical Endpoints](#statistical-endpoints)
- [Request Parameters](#request-parameters)
- [Response Formats](#response-formats)
- [Error Responses](#error-responses)
- [HTTP Status Codes](#http-status-codes)
- [OpenAPI Specification](#openapi-specification)
- [Security Considerations](#security-considerations)

---

## Processing Endpoints

### Process CSV File

Process a CSV file containing bank transactions and receive detailed transaction data grouped by category and month. Returns DataTables-compatible JSON for client-side rendering and export.

**Endpoint:**
```
POST /api/v2/process
```

**Description:**
Upload a CSV file with bank transactions. Optionally provide a YAML configuration file to customize processing. Returns aggregated transaction data with drilldown capabilities.

**Method:** `POST`

**Content-Type:** `multipart/form-data`

**Curl Example:**
```bash
# Basic usage - get transaction details plus summary
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv"

# With date filtering
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "start_date=2024.01.01" \
  -F "end_date=2024.12.31"

# With custom config and ML categorization
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "config_file=@config.yml" \
  -F "ml_enabled=true"

# Filter by specific category
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "category_filter=grocery"

# With CSV profile selection
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "csv_profile_id=otp-hu"

# With cache TTL (1800 seconds = 30 minutes)
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "cache_ttl=1800"

# With custom date format
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "date_format=%Y-%m-%d"
```

**Status Codes:**
- `200` - Successfully processed
- `400` - Bad request (missing file, invalid parameters)
- `422` - Unprocessable entity (CSV parsing error, validation failed)
- `500` - Internal server error

---

## Results Endpoints

### Get Processing Results

Retrieve cached processing results for frontend rendering with drilldown URLs.

**Endpoint:**
```
GET /api/v2/results/<result_id>
```

**Description:**
Get the full processing results including accounts data, statistical highlights, and navigation URLs for drilldown views. The `result_id` is returned in the response metadata when processing a CSV file.

**Method:** `GET`

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the cached processing result |

**Curl Example:**
```bash
# Get results for a specific processing run
curl -X GET http://localhost:5000/api/v2/results/550e8400-e29b-41d4-a716-446655440000
```

**Status Codes:**
- `200` - Successfully retrieved results
- `404` - Results not found or expired
- `500` - Internal server error

---

## Drilldown Endpoints

The drilldown endpoints enable hierarchical navigation through transaction data: Category -> Month -> Transactions.

### Get Category Months

Get month-by-month aggregation data for a specific category within an account.

**Endpoint:**
```
GET /api/v2/results/<result_id>/accounts/<account_id>/categories/<category_id>/months
```

**Description:**
Returns aggregated totals for each month within a specific category, enabling time-based analysis.

**Method:** `GET`

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the cached processing result |
| `account_id` | Yes | string | Account identifier |
| `category_id` | Yes | string | Category identifier (e.g., 'grocery', 'clothes') |

**Curl Example:**
```bash
curl -X GET "http://localhost:5000/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/categories/grocery/months"
```

**Status Codes:**
- `200` - Successfully retrieved category months
- `404` - Result, account, or category not found
- `500` - Internal server error

---

### Get Month Categories

Get category-by-category aggregation data for a specific month within an account.

**Endpoint:**
```
GET /api/v2/results/<result_id>/accounts/<account_id>/months/<month_id>/categories
```

**Description:**
Returns aggregated totals for each category within a specific month, enabling category-based analysis.

**Method:** `GET`

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the cached processing result |
| `account_id` | Yes | string | Account identifier |
| `month_id` | Yes | string | Month identifier (Unix timestamp) |

**Curl Example:**
```bash
curl -X GET "http://localhost:5000/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/months/1704067200/categories"
```

**Status Codes:**
- `200` - Successfully retrieved month categories
- `404` - Result, account, or month not found
- `500` - Internal server error

---

### Get Category Month Transactions

Get individual transaction details for a specific category and month within an account.

**Endpoint:**
```
GET /api/v2/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions
```

**Description:**
Returns the raw transaction details for drilling down to the individual transaction level.

**Method:** `GET`

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the cached processing result |
| `account_id` | Yes | string | Account identifier |
| `category_id` | Yes | string | Category identifier (e.g., 'grocery', 'clothes') |
| `month_id` | Yes | string | Month identifier (Unix timestamp) |

**Curl Example:**
```bash
curl -X GET "http://localhost:5000/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/categories/grocery/months/1704067200/transactions"
```

**Status Codes:**
- `200` - Successfully retrieved transactions
- `404` - Result, account, category, or month not found
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
Returns the full list of CategoryDefinition objects that the frontend can use for translating category IDs to display names client-side. Each category has an `id` field (for API usage) and a `default_name` field (for display, can be localized).

**Method:** `GET`

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

**Description:**
Returns a filtered list of CategoryDefinition objects for categories that contribute to cost of living metrics.

**Method:** `GET`

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

Retrieve all available CSV profile definitions.

**Endpoint:**
```
GET /api/v2/csv-profiles
```

**Description:**
Returns a list of all available CSV profiles with their metadata, including ID, name, description, version, and CSV configuration.

**Method:** `GET`

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

Retrieve the details of a specific CSV profile by its ID.

**Endpoint:**
```
GET /api/v2/csv-profiles/<profile_id>
```

**Description:**
Returns the full configuration details of a specific CSV profile.

**Method:** `GET`

**URL Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `profile_id` | Yes | string | The unique identifier of the CSV profile (e.g., 'otp-hu', 'kh-hu') |

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

Recalculate statistical highlights with custom algorithm and direction settings.

**Endpoint:**
```
POST /api/v2/recalculate-statistics
```

**Description:**
Recalculate the statistical analysis for a cached processing result using specified algorithms and analysis direction. Updates the cache with new statistical metadata.

**Method:** `POST`

**Content-Type:** `application/json`

**Request Body:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `result_id` | Yes | string | UUID of the cached processing result |
| `algorithms` | Yes | array[string] | List of algorithm names (e.g., ['iqr', 'pareto']) |
| `direction` | Yes | string | Analysis direction: 'rows' or 'columns' |

**Curl Example:**
```bash
# Recalculate with IQR and Pareto algorithms for column-based analysis
curl -X POST http://localhost:5000/api/v2/recalculate-statistics \
  -H "Content-Type: application/json" \
  -d '{"result_id": "550e8400-e29b-41d4-a716-446655440000", "algorithms": ["iqr", "pareto"], "direction": "columns"}'

# Row-based analysis with only IQR
curl -X POST http://localhost:5000/api/v2/recalculate-statistics \
  -H "Content-Type: application/json" \
  -d '{"result_id": "550e8400-e29b-41d4-a716-446655440000", "algorithms": ["iqr"], "direction": "rows"}'
```

**Status Codes:**
- `200` - Successfully recalculated statistics
- `400` - Bad request (missing parameters, invalid values)
- `404` - Result data not found
- `500` - Internal server error

---

## Request Parameters

### Processing Endpoint Parameters (`POST /api/v2/process`)

All parameters are submitted as `multipart/form-data`.

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `csv_file` | Yes | file | - | CSV file containing bank transactions. Required. |
| `config_file` | No | file | - | Optional YAML configuration file. Uses default config if not provided. |
| `start_date` | No | string | - | Filter start date. Format matches config's `date_attribute_format` (default: `%Y.%m.%d`). Example: `2024.01.01` |
| `end_date` | No | string | - | Filter end date. Format matches config's `date_attribute_format`. Example: `2024.12.31` |
| `date_format` | No | string | From config | Date format string (Python strptime format). Overrides config default. Example: `%Y-%m-%d` |
| `ml_enabled` | No | boolean | `false` | Enable ML-based categorization instead of regex patterns. Accepts `true` or `false` as string. |
| `category_filter` | No | string | - | Filter results to specific category by `category_id` (e.g., `grocery`). Use `/api/v2/categories` to see available IDs. |
| `cache_ttl` | No | integer | Backend default | Cache TTL in seconds. Use `0` for never expire. Example: `1800` (30 minutes) |
| `csv_profile_id` | No | string | Default profile | CSV profile ID to use for parsing (e.g., `otp-hu`, `kh-hu`). Uses default if not provided. |

---

## Response Formats

### Process Endpoint Response (`POST /api/v2/process`)

Returns aggregated transaction data grouped by category and month, with detailed transaction information.

```json
{
  "data": [
    {
      "category_id": "grocery",
      "total": {
        "display": "HUF -45,600.50",
        "raw": -45600.50
      },
      "date": {
        "display": "January",
        "timestamp": 1704067200
      },
      "details": [
        {
          "date": {
            "display": "2024-01-15",
            "timestamp": 1705276800
          },
          "amount": {
            "display": "-12,500.00",
            "raw": -12500.00
          },
          "merchant": "TESCO",
          "currency": "HUF",
          "type": "card_payment",
          "confidence": 0.95,
          "notice": "Payment for groceries"
        }
      ]
    }
  ],
  "metadata": {
    "result_id": "550e8400-e29b-41d4-a716-446655440000",
    "row_count": 145,
    "processing_time": 0.456,
    "ml_enabled": false,
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "cache_ttl": 1800
  }
}
```

**Field Descriptions:**

- `data`: Array of aggregated rows by category and month
- `category_id`: Category identifier (use `/api/v2/categories` to get display names)
- `total`: Object with `display` (formatted string) and `raw` (numeric value)
- `date`: Object with `display` (formatted date/month) and `timestamp` (Unix epoch)
- `details`: Array of individual transaction objects
- `metadata.result_id`: UUID for retrieving results via `/api/v2/results/<result_id>`
- `metadata.row_count`: Number of transactions processed
- `metadata.processing_time`: Processing time in seconds
- `metadata.ml_enabled`: Whether ML categorization was used
- `metadata.date_range`: Applied date filter range
- `metadata.cache_ttl`: Cache timeout in seconds

---

### Results Endpoint Response (`GET /api/v2/results/<result_id>`)

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "accounts": [
    {
      "id": "account_1",
      "name": "Primary Account",
      "formatted_id": "12345678-12345678",
      "currency": "HUF",
      "dt_response": {
        "data": [],
        "metadata": {}
      }
    }
  ],
  "highlights": {
    "row_abc123": ["outlier", "pareto"]
  },
  "drilldown_urls_by_account": {
    "account_1": {
      "account_id": "account_1",
      "category_urls": {
        "grocery": {
          "category_url": "/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/categories/grocery/months",
          "category_id": "grocery"
        }
      },
      "month_urls": {},
      "cell_urls": {}
    }
  }
}
```

---

### Drilldown Endpoint Responses

#### Category Months (`GET /api/v2/results/.../categories/.../months`)

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "account_1",
  "account_name": "Primary Account",
  "account_formatted_id": "12345678-12345678",
  "account_currency": "HUF",
  "category_id": "grocery",
  "data": [
    {
      "month_timestamp": 1704067200,
      "total": {
        "display": "HUF -500.00",
        "raw": -500.0
      },
      "row_id": "row_001",
      "cell_url": "/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/categories/grocery/months/1704067200/transactions"
    }
  ],
  "highlights": {
    "row_001": ["outlier"]
  }
}
```

#### Month Categories (`GET /api/v2/results/.../months/.../categories`)

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "account_1",
  "account_name": "Primary Account",
  "account_formatted_id": "12345678-12345678",
  "account_currency": "HUF",
  "month_id": "1672531200",
  "month_timestamp": 1672531200,
  "data": [
    {
      "category_id": "grocery",
      "total": {
        "display": "HUF -150.00",
        "raw": -150.0
      },
      "row_id": "row_001",
      "category_url": "/api/v2/results/550e8400-e29b-41d4-a716-446655440000/accounts/account_1/categories/grocery/months/1672531200/transactions"
    }
  ],
  "highlights": null
}
```

#### Category Month Transactions (`GET /api/v2/results/.../categories/.../months/.../transactions`)

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "account_1",
  "account_name": "Primary Account",
  "account_formatted_id": "12345678-12345678",
  "account_currency": "HUF",
  "category_id": "grocery",
  "month_id": "1672531200",
  "month_timestamp": 1672531200,
  "data": [
    {
      "date": {
        "display": "2023-01-01",
        "timestamp": 1672531200
      },
      "amount": {
        "display": "HUF -100.00",
        "raw": -100.0
      },
      "merchant": "Test Merchant 1",
      "currency": "HUF",
      "type": "card_payment",
      "confidence": 0.95,
      "notice": "Payment for invoice #1234",
      "row_id": "detail_1",
      "category_id": "grocery",
      "month_id": "1672531200"
    }
  ],
  "highlights": null
}
```

---

## Error Responses

All API endpoints return structured error responses in JSON format.

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": 404,
    "message": "Results expired, please re-process",
    "details": "Result ID 550e8400-e29b-41d4-a716-446655440000 not found in cache"
  }
}
```

**Field Descriptions:**

- `status`: Response status (always `"error"` for error responses)
- `error.code`: HTTP status code (integer)
- `error.message`: Human-readable error message
- `error.details`: Additional error details (optional, may be null)

---

## HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | Success | Request processed successfully |
| `400` | Bad Request | Missing required file, invalid parameters, validation error |
| `404` | Not Found | Result not found, CSV profile not found |
| `422` | Unprocessable Entity | CSV parsing error, invalid date format, date range validation failed |
| `500` | Internal Server Error | Server-side processing error |

---

## OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available for programmatic access and documentation generation.

**Endpoint:**
```
GET /api/v2/openapi.json
```

**Description:**
Returns the full OpenAPI specification in JSON format. This can be used with OpenAPI-compatible tools for documentation generation, client code generation, or testing.

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
- Input validation (file types, MIME types, parameter validation)
- Secure filename handling (prevents path traversal)
- CSV file validation (structure, required columns)
- Date format and range validation
- No rate limiting
- No authentication
- No API keys
- CORS enabled for development (`http://localhost:3000`, `http://127.0.0.1:3000`)
- Production CORS configurable via Flask-CORS

**Recommendations for Production:**
- Add rate limiting to prevent abuse
- Consider adding API key authentication
- Configure CORS origins appropriately for your frontend domain
- Use HTTPS in production

---

## Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/process` | Process CSV file and return detailed transaction data |
| `GET` | `/api/v2/results/<result_id>` | Get cached processing results with drilldown URLs |
| `GET` | `/api/v2/results/.../accounts/.../categories/.../months` | Get months for a category |
| `GET` | `/api/v2/results/.../accounts/.../months/.../categories` | Get categories for a month |
| `GET` | `/api/v2/results/.../accounts/.../categories/.../months/.../transactions` | Get transactions for category and month |
| `POST` | `/api/v2/recalculate-statistics` | Recalculate statistics with custom settings |
| `GET` | `/api/v2/categories` | Get all category definitions |
| `GET` | `/api/v2/categories/cost-of-living` | Get cost of living categories |
| `GET` | `/api/v2/csv-profiles` | List all CSV profiles |
| `GET` | `/api/v2/csv-profiles/<profile_id>` | Get specific CSV profile |
| `GET` | `/api/v2/openapi.json` | Get OpenAPI specification |
