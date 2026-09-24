/**
 * API Response Type Definitions for What's the Damage Frontend
 *
 * These TypeScript interfaces define the exact contract for each API endpoint response,
 * ensuring type safety and consistency with backend Pydantic models.
 *
 * Backend counterparts are defined in:
 * - src/whatsthedamage/models/api/responses.py (API v2 Response DTOs)
 * - src/whatsthedamage/models/domain/dt_models.py (Data models)
 */

// ============================================================================
// Common Types
// ============================================================================

/**
 * Display and raw value pair (e.g., formatted currency with numeric value)
 */
export interface DisplayRawField {
  display: string;
  raw: number;
}

/**
 * Date with display format and timestamp
 * @deprecated Use ISO 8601 date strings directly instead.
 * This type is kept for backward compatibility but is no longer used in API responses.
 */
export interface DateField {
  display: string;
  timestamp: number;
}

// ============================================================================
// Data Models (from dt_models.py)
// ============================================================================

/**
 * Unified transaction detail model - consolidates DetailRow and TransactionDetail.
 * Replaces the previous DetailRow and TransactionDetailResponse interfaces.
 * Uses ISO 8601 date strings instead of DateField objects.
 */
export interface TransactionDetail {
  row_id: string;
  date: string; // ISO 8601 date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
  amount: DisplayRawField;
  merchant: string;
  currency: string;
  account: string;
  type?: string | null;
  confidence?: number | null;
  notice?: string | null;
  // API drilldown context fields
  category_id?: string | null;
  month_id?: string | null;
}

/**
 * Aggregated row: transactions grouped by category and date
 * Uses ISO 8601 date strings instead of DateField objects.
 */
export interface AggregatedRow {
  row_id: string;
  category_id: string;
  total: DisplayRawField;
  date: string; // ISO 8601 date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
  details: TransactionDetail[];
  is_calculated?: boolean;
}

// DetailRow is now an alias to TransactionDetail
export type DetailRow = TransactionDetail;

/**
 * Processing metadata
 */
interface ProcessingMetadata {
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
type StatisticalHighlights = Record<string, string[]> | {};

// ============================================================================
// Account/Results Types
// ============================================================================

/**
 * Unified Account model - matches backend Account Pydantic model
 * Replaces previous AccountData and AccountDataResponse interfaces
 */
export interface Account {
  id: string;
  name: string;
  formatted_id: string;
  currency: string;
  data?: AggregatedRow[];  // Previously was dt_response: { data: AggregatedRow[] }
  result_id?: string;
  metadata?: unknown | null;
}

// ============================================================================
// API Response Types (matching backend Pydantic models from api_responses.py)
// ============================================================================

// -----------------------------------------------------------------------------
// Transactions Endpoint: POST /api/v2/transactions
// -----------------------------------------------------------------------------

/**
 * Response from POST /api/v2/transactions
 *
 * Contains processed transaction data grouped by category and month,
 * plus processing metadata.
 */
export interface DetailedResponse {
  data: AggregatedRow[];
  metadata: ProcessingMetadata;
}

// -----------------------------------------------------------------------------
// Results Endpoint: GET /api/v2/results/<result_id>
// -----------------------------------------------------------------------------

/**
 * URL info for category drilldown
 */
interface DrilldownUrlInfo {
  category_url: string;
  category_id: string;
}

/**
 * URL info for month drilldown
 */
interface MonthUrlInfo {
  month_url: string;
  month_id: string;
}

/**
 * URL info for cell/transaction drilldown
 */
interface CellUrlInfo {
  cell_url: string;
  category_id: string;
  month_id: string;
}

/**
 * All drilldown URLs for a single account
 */
interface DrilldownUrls {
  account_id: string | null;
  category_urls: Record<string, DrilldownUrlInfo>;
  month_urls: Record<string, MonthUrlInfo>;
  cell_urls: Record<string, CellUrlInfo>;
}

/**
 * Response from GET /api/v2/results/<result_id>
 *
 * Contains cached processing results with accounts data and drilldown URLs.
 * Now uses simplified structure with direct Account array instead of nested wrappers.
 */
export interface ResultsApiResponse {
  result_id: string;
  accounts: Account[];  // Changed from accounts_data: AccountsDataResponse
  highlights: StatisticalHighlights;
  drilldown_urls_by_account: Record<string, DrilldownUrls>;
}

/**
 * URL info for category drilldown
 */
interface DrilldownUrlInfo {
  category_url: string;
  category_id: string;
}

/**
 * URL info for month drilldown
 */
interface MonthUrlInfo {
  month_url: string;
  month_id: string;
}

/**
 * URL info for cell/transaction drilldown
 */
interface CellUrlInfo {
  cell_url: string;
  category_id: string;
  month_id: string;
}

/**
 * All drilldown URLs for a single account
 */
interface DrilldownUrls {
  account_id: string | null;
  category_urls: Record<string, DrilldownUrlInfo>;
  month_urls: Record<string, MonthUrlInfo>;
  cell_urls: Record<string, CellUrlInfo>;
}

// -----------------------------------------------------------------------------
// Category Definitions
// -----------------------------------------------------------------------------

/**
 * Category definition from the backend
 * Fetched via GET /api/v2/categories
 */
export interface CategoryDefinition {
  id: string;
  default_name: string;
  patterns: string[];
}

// -----------------------------------------------------------------------------
// Drilldown Endpoints
// -----------------------------------------------------------------------------

/**
 * Data for a single month in category months response
 * Uses ISO 8601 date string instead of timestamp.
 */
export interface MonthData {
  month_date: string; // ISO 8601 date string (YYYY-MM-DD)
  total: DisplayRawField;
  row_id: string;
  cell_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months
 *
 * Returns month-by-month aggregation for a specific category.
 * Uses ISO 8601 date strings instead of timestamps.
 */
export interface CategoryMonthsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  account_formatted_id: string;
  account_currency: string;
  category_id: string;
  data: MonthData[];
  highlights?: StatisticalHighlights;
}

/**
 * Data for a single category in month categories response
 */
export interface CategoryData {
  category_id: string;
  total: DisplayRawField;
  row_id: string;
  category_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/months/<m>/categories
 *
 * Returns category-by-category aggregation for a specific month.
 * Uses ISO 8601 date string instead of timestamp.
 */
export interface MonthCategoriesApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  account_formatted_id: string;
  account_currency: string;
  month_id: string;
  month_date: string; // ISO 8601 date string (YYYY-MM-DD)
  data: CategoryData[];
  highlights?: StatisticalHighlights;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions
 *
 * Returns individual transaction details for a specific category and month.
 * Uses ISO 8601 date string instead of timestamp.
 */
export interface CategoryMonthTransactionsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  account_formatted_id: string;
  account_currency: string;
  category_id: string;
  month_id: string;
  month_date: string; // ISO 8601 date string (YYYY-MM-DD)
  data: TransactionDetail[];
  highlights?: StatisticalHighlights;
}

// -----------------------------------------------------------------------------
// Recalculate Statistics Endpoint: POST /api/v2/recalculate-statistics
// -----------------------------------------------------------------------------

/**
 * Response from POST /api/v2/recalculate-statistics
 *
 * Returns updated statistical highlights with new algorithm settings.
 */
export interface RecalculateApiResponse {
  status: string;
  result_id: string;
  highlights: StatisticalHighlights;
  algorithms: string[];
  direction: 'columns' | 'rows';
}

// -----------------------------------------------------------------------------
// CSV Profile Types
// -----------------------------------------------------------------------------

/**
 * CSV configuration for a profile
 */
export interface CsvConfig {
  dialect: string;
  delimiter: string;
  date_attribute_format: string;
  attribute_mapping: Record<string, string>;
}

/**
 * CSV profile definition with metadata
 * Fetched via GET /api/v2/csv-profiles
 */
export interface CsvProfile {
  id: string;
  name: string;
  description: string;
  version: string;
  csv_config: CsvConfig;
  is_default: boolean;
}

/**
 * Schema information for CSV profile format
 * Fetched via GET /api/v2/csv-profiles/schema
 */
export interface CsvProfileSchema {
  description: string;
  required_fields: string[];
  optional_fields: string[];
  csv_config_required: string[];
  attribute_mapping_required_keys: string[];
  example: Record<string, unknown>;
  notes: string[];
}

// -----------------------------------------------------------------------------
// Processing Results Endpoint: GET /api/v2/processing-results
// -----------------------------------------------------------------------------

/**
 * List item for user's processing results
 * Fetched via GET /api/v2/processing-results
 */
export interface ProcessingResultListItem {
  id: string;  // This is result_id
  csv_profile_id: string | null;
  row_count: number | null;
  processing_time: number | null;
  ml_enabled: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string | null;
  // updated_at removed as per requirement
}

/**
 * Processing result metadata (replaces ResultsApiResponse data structure)
 * Fetched via GET /api/v2/processing-results/<result_id>
 */
export interface ProcessingResultMetadata {
  result_id: string;
  user_id: number;
  csv_profile_id: string | null;
  row_count: number | null;
  processing_time: number | null;
  ml_enabled: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string | null;
  transactions_url: string;  // Link to /transactions endpoint
}

/**
 * Response from POST /api/v2/processing-results
 * Contains processing metadata (flat structure, not wrapped in metadata)
 */
export interface ProcessingResultCreationResponse {
  result_id: string;
  user_id: number | string;
  csv_profile_id: string | null;
  row_count: number | null;
  processing_time: number;
  ml_enabled: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  transactions_count: number;
  message: string;
}

/**
 * Transaction entity for list responses
 */
export interface TransactionListItem {
  id: number;
  user_id: number;
  result_id: string | null;
  date: string; // ISO 8601 date-time string (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD)
  transaction_type: string;
  original_partner: string;
  amount: number;
  currency: string;
  account: string;
  deduplication_hash: string;
  category_id: string | null;
  partner: string | null;
  notice: string | null;
  confidence: number | null;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Transaction list response with pagination
 */
export interface TransactionListResponse {
  transactions: TransactionListItem[];
  total_count: number;
  limit: number;
  offset: number;
}

/**
 * Aggregated transaction data for drilldown views
 */
export interface AggregatedTransactionsResponse {
  result_id: string;
  account?: string;
  category_id?: string;
  month?: string;
  group_by: string;
  groups: Record<string, TransactionListItem[]>;
  highlights: Record<string, string[]>;
  total_count: number;
}

