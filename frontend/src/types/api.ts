/**
 * API Response Type Definitions for What's the Damage Frontend
 *
 * These TypeScript interfaces define the exact contract for each API endpoint response,
 * ensuring type safety and consistency with backend Pydantic models.
 *
 * Backend counterparts are defined in:
 * - src/whatsthedamage/models/api_responses.py (API v2 Response DTOs)
 * - src/whatsthedamage/models/dt_models.py (Data models)
 */

// ============================================================================
// Common Types
// ============================================================================

/**
 * Display and raw value pair (e.g., formatted currency with numeric value)
 */
interface _DisplayRawField {
  display: string;
  raw: number | string;
}

/**
 * Date with display format and timestamp
 */
interface _DateField {
  display: string;
  timestamp: number;
}

/**
 * Standard error response format for all API v2 endpoints
 *
 * Returned for non-200 status codes.
 */
interface _ErrorApiResponse {
  code: number;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Standard API response envelope for new endpoints (recommended)
 *
 * Provides a consistent structure for all API responses:
 * - status: Operation status ('success' or 'error')
 * - data: The endpoint-specific response payload
 * - meta: Response metadata (timestamp, request_id, version, etc.)
 * - links: Hypermedia navigation links (self, related resources)
 * - timestamp: Response generation timestamp in UTC
 *
 * Backend counterpart: ApiEnvelope<T> in models/api_responses.py
 *
 * @example
 * ```typescript
 * const response = await fetch('/api/v2/new-endpoint');
 * const envelope: ApiEnvelope<SomeData> = await response.json();
 * console.log(envelope.status); // 'success'
 * console.log(envelope.data); // SomeData payload
 * console.log(envelope.meta.request_id); // request identifier
 * ```
 */
type _ApiEnvelope<T = unknown> = {
  status: 'success' | 'error';
  data: T;
  meta: Record<string, unknown>;
  links: Record<string, string>;
  timestamp: string; // ISO 8601 datetime string
};

// ============================================================================
// Data Models (from dt_models.py)
// ============================================================================

/**
 * A single detailed transaction row
 */
interface _DetailRow {
  row_id: string;
  date: _DateField;
  amount: _DisplayRawField;
  merchant: string;
  currency: string;
  account: string;
  type?: string | null;
  confidence?: number | null;
  notice?: string | null;
}

/**
 * Aggregated row: transactions grouped by category and date
 */
interface _AggregatedRow {
  row_id: string;
  category: string;
  total: _DisplayRawField;
  date: _DateField;
  details: _DetailRow[];
  is_calculated?: boolean;
}

/**
 * Processing metadata
 */
interface _ProcessingMetadata {
  result_id: string;
  row_count: number;
  processing_time: number;
  ml_enabled: boolean;
  date_range?: string;
}

/**
 * Statistical highlights for a single cell/row
 * Maps row_id to list of highlight types (e.g., ['outlier', 'pareto'])
 */
type _StatisticalHighlights = Record<string, string[]>;

// ============================================================================
// Account/Results Types
// ============================================================================

/**
 * Account data structure for results
 */
export interface AccountData {
  id: string;
  formatted_id: string;
  currency: string;
  transactions: _TransactionData[];
  summary: _AccountSummary;
}

/**
 * Individual transaction data
 */
interface _TransactionData {
  id: string;
  date: string;
  amount: number;
  currency: string;
  description: string;
  merchant: string;
  category: string;
  category_confidence: number;
  type: string;
  account_id: string;
}

/**
 * Account summary statistics
 */
interface _AccountSummary {
  total_transactions: number;
  total_amount: number;
  categories: _CategorySummary[];
}

/**
 * Category-level summary
 */
interface _CategorySummary {
  category: string;
  count: number;
  total_amount: number;
  percentage: number;
}

// ============================================================================
// API Response Types (matching backend Pydantic models from api_responses.py)
// ============================================================================

// -----------------------------------------------------------------------------
// Process Endpoint: POST /api/v2/process
// -----------------------------------------------------------------------------

/**
 * Response from POST /api/v2/process
 *
 * Contains processed transaction data grouped by category and month,
 * plus processing metadata.
 */
export interface _ProcessApiResponse {
  data: _AggregatedRow[];
  metadata: _ProcessingMetadata;
}

// -----------------------------------------------------------------------------
// Results Endpoint: GET /api/v2/results/<result_id>
// -----------------------------------------------------------------------------

/**
 * Data for a single account in results response
 */
interface _AccountDataResponse {
  id: string;
  name: string;
  dt_response: {
    data: _AggregatedRow[];
  };
}

/**
 * Container for all accounts data
 */
interface _AccountsDataResponse {
  accounts: _AccountDataResponse[];
  highlights: _StatisticalHighlights;
}

/**
 * URL info for category drilldown
 */
interface _DrilldownUrlInfo {
  category_url: string;
  category_id: string;
}

/**
 * URL info for month drilldown
 */
interface _MonthUrlInfo {
  month_url: string;
  month_id: string;
}

/**
 * URL info for cell/transaction drilldown
 */
interface _CellUrlInfo {
  cell_url: string;
  category_id: string;
  month_id: string;
}

/**
 * All drilldown URLs for a single account
 */
interface _DrilldownUrls {
  account_id: string | null;
  category_urls: Record<string, _DrilldownUrlInfo>;
  month_urls: Record<string, _MonthUrlInfo>;
  cell_urls: Record<string, _CellUrlInfo>;
}

/**
 * Response from GET /api/v2/results/<result_id>
 *
 * Contains cached processing results with accounts data and drilldown URLs.
 */
export interface _ResultsApiResponse {
  result_id: string;
  accounts_data: _AccountsDataResponse;
  drilldown_urls_by_account: Record<string, _DrilldownUrls>;
}

// -----------------------------------------------------------------------------
// Drilldown Endpoints
// -----------------------------------------------------------------------------

/**
 * Data for a single month in category months response
 */
export interface MonthData {
  month: string;
  month_timestamp: number;
  total: _DisplayRawField;
  row_id: string;
  cell_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months
 *
 * Returns month-by-month aggregation for a specific category.
 */
export interface _CategoryMonthsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  category_id: string;
  category_name: string;
  data: MonthData[];
  highlights?: _StatisticalHighlights;
}

/**
 * Data for a single category in month categories response
 */
export interface CategoryData {
  category: string;
  total: _DisplayRawField;
  row_id: string;
  category_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/months/<m>/categories
 *
 * Returns category-by-category aggregation for a specific month.
 */
export interface _MonthCategoriesApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  month_id: string;
  month_name: string;
  data: CategoryData[];
  highlights?: _StatisticalHighlights;
}

/**
 * Data for a single transaction in drilldown response
 */
interface _TransactionDetailResponse {
  date: { display: string };
  amount: _DisplayRawField;
  merchant: string;
  row_id: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions
 *
 * Returns individual transaction details for a specific category and month.
 */
export interface _CategoryMonthTransactionsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  category_id: string;
  category_name: string;
  month_id: string;
  month_name: string;
  data: _TransactionDetailResponse[];
  highlights?: _StatisticalHighlights;
}

// -----------------------------------------------------------------------------
// Recalculate Statistics Endpoint: POST /api/v2/recalculate-statistics
// -----------------------------------------------------------------------------

/**
 * Response from POST /api/v2/recalculate-statistics
 *
 * Returns updated statistical highlights with new algorithm settings.
 */
interface _RecalculateApiResponse {
  status: string;
  result_id: string;
  highlights: _StatisticalHighlights;
  algorithms: string[];
  direction: 'columns' | 'rows';
}

