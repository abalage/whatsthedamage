# REST API Documentation

The REST API provides programmatic access to transaction processing with JSON responses.

## API Endpoints

### Base URL
```
http://localhost:5000/api
```

### Available Versions

**API v1** - Summary data only (recommended for most use cases)
```
POST /api/v1/process
```
Returns aggregated totals by category. Small payloads, fast responses.

**API v2** - Detailed transaction data
```
POST /api/v2/process
```
Returns individual transactions plus summary. Large payloads, use when you need transaction details.

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

## Interactive API Documentation

The API includes **Swagger UI** for interactive testing and documentation:

```
# View v1 API documentation
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
