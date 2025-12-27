# REST API Documentation

The REST API provides programmatic access to transaction processing with JSON responses.

## ⚠️ Deprecation Notice

**API v1 is deprecated** and will be removed in version **v0.10.0**. 

Please migrate to **API v2** for:
- ✅ Multi-account support
- ✅ Canonical DataTables-compatible types
- ✅ Detailed transaction-level data
- ✅ Unified processing pipeline

See [Migration Guide](#migration-guide) below for details on upgrading.

## API Endpoints

### Base URL
```
http://localhost:5000/api
```

### Available Versions

**API v2** - Detailed transaction data (recommended)
```
POST /api/v2/process
```
Returns individual transactions plus summary with multi-account support. Use when you need transaction details or multi-account handling.

**API v1** - Summary data only (⚠️ deprecated)
```
POST /api/v1/process
```
Returns aggregated totals by category. Small payloads, fast responses. **Will be removed in v0.10.0.**

## Quick Start Examples

### Using curl (v1 - Summary Only)

```bash
# Basic usage - summary totals by category
curl -X POST http://localhost:5000/api/v1/process \
  -F "csv_file=@transactions.csv"

# With date filtering
curl -X POST http://localhost:5000/api/v1/process \
  -F "csv_file=@transactions.csv" \
  -F "start_date=2024-01-01" \
  -F "end_date=2024-12-31"

# With custom config and ML categorization
curl -X POST http://localhost:5000/api/v1/process \
  -F "csv_file=@transactions.csv" \
  -F "config_file=@config.yml" \
  -F "ml_enabled=true"

# Filter by specific category
curl -X POST http://localhost:5000/api/v1/process \
  -F "csv_file=@transactions.csv" \
  -F "category_filter=Grocery"
```

### Using curl (v2 - Detailed Data)

```bash
# Get transaction details plus summary
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv"
```

## Request Parameters

All API endpoints accept multipart/form-data with the following parameters:

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `csv_file` | ✅ Yes | file | CSV file with bank transactions |
| `config_file` | ❌ No | file | YAML configuration file (uses default if not provided) |
| `start_date` | ❌ No | string | Filter start date (format: YYYY-MM-DD) |
| `end_date` | ❌ No | string | Filter end date (format: YYYY-MM-DD) |
| `ml_enabled` | ❌ No | boolean | Enable ML categorization (default: false) |
| `category_filter` | ❌ No | string | Filter by specific category (e.g., "Grocery") |
| `language` | ❌ No | string | Output language: "en" or "hu" (default: "en") |

## Response Format

### v1 Response (Summary Only)

```json
{
  "data": {
    "Balance": 129576.00,
    "Vehicle": -106151.00,
    "Grocery": -172257.00,
    "Deposit": 725313.00,
    "Other": -86411.00
  },
  "metadata": {
    "row_count": 145,
    "processing_time": 0.234,
    "ml_enabled": false,
    "date_range": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    }
  }
}
```

### v2 Response (Detailed)

```json
{
  "summary": {
    "Balance": 129576.00,
    "Grocery": -172257.00
  },
  "transactions": [
    {
      "date": "2024-01-15",
      "partner": "TESCO",
      "amount": -15420.00,
      "currency": "HUF",
      "category": "Grocery"
    }
  ],
  "metadata": {
    "row_count": 145,
    "processing_time": 0.456,
    "ml_enabled": false
  }
}
```

## Error Responses

All API endpoints return structured error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "No CSV file provided",
    "details": {
      "field": "csv_file",
      "reason": "required field missing"
    }
  }
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | Success | Request processed successfully |
| `400` | Bad Request | Missing required file, invalid parameters |
| `422` | Unprocessable Entity | CSV parsing error, invalid date format |
| `500` | Internal Server Error | Server-side processing error |

## Migration Guide

### Migrating from API v1 to v2

API v1 will be removed in v0.10.0. Follow this guide to migrate your integration.

#### Key Differences

| Aspect | v1 (deprecated) | v2 (recommended) |
|--------|----------------|------------------|
| **Response structure** | `data: Dict[str, float]` | `data: List[AggregatedRow]` |
| **Category access** | `data["Grocery"]` | Iterate array to find category |
| **Amount format** | `float` | `{display: string, raw: float}` |
| **Multi-account** | Single merged summary | Per-account separation |
| **Transaction details** | ❌ Not available | ✅ Available in `details` |
| **Date fields** | N/A | `{display: string, timestamp: int}` |

#### Breaking Changes

**1. Response Data Structure**

v1 returns a flat dictionary:
```json
{
  "data": {
    "Grocery": -172257.00,
    "Vehicle": -106151.00
  }
}
```

v2 returns an array of aggregated rows:
```json
{
  "data": [
    {
      "category": "Grocery",
      "total": {"display": "-172,257.00", "raw": -172257.00},
      "month": {"display": "January", "timestamp": 1704067200},
      "details": [...]
    }
  ]
}
```

**2. Accessing Category Totals**

v1:
```python
total_groceries = response["data"]["Grocery"]
```

v2:
```python
# Find category in array
grocery_row = next(
    (row for row in response["data"] if row["category"] == "Grocery"),
    None
)
total_groceries = grocery_row["total"]["raw"] if grocery_row else 0
```

**3. Multi-Account Handling**

v1 merges all accounts into single summary.

v2 separates by account - each `AggregatedRow` contains account info in nested `details`:
```json
{
  "details": [
    {
      "account": "12345678",
      "amount": {"display": "-50.00", "raw": -50.0},
      ...
    }
  ]
}
```

**4. Display vs Raw Values**

v1 returns raw numbers only.

v2 provides both formatted display strings and raw values for sorting/calculations:
```json
{
  "amount": {
    "display": "-1,234.56",  // Use for display
    "raw": -1234.56          // Use for calculations
  }
}
```

#### Migration Steps

1. **Update endpoint URL**: Change `/api/v1/process` → `/api/v2/process`
2. **Update response parsing**: Iterate over `data` array instead of accessing dict keys
3. **Use raw values**: Access amounts via `row["total"]["raw"]` instead of direct float
4. **Handle multiple months**: v2 returns separate rows per category+month combination
5. **Test thoroughly**: v2 payloads are larger; ensure your client handles increased data size

## Interactive API Documentation

The API includes **Swagger UI** for interactive testing and documentation:

```
# View v1 API documentation (deprecated)
http://localhost:5000/api/docs?version=v1

# View v2 API documentation
http://localhost:5000/api/docs?version=v2

# Download OpenAPI spec (v1)
http://localhost:5000/api/v1/openapi.json

# Download OpenAPI spec (v2)
http://localhost:5000/api/v2/openapi.json
```

Open the `/api/docs` endpoint in your browser to:
- See all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- Download OpenAPI specifications

## Security Considerations

**Current state:**
- ✅ Input validation (file types, parameters)
- ✅ Secure filename handling
- ❌ No rate limiting
- ❌ No authentication
- ❌ No API keys
- ❌ No CORS restrictions
