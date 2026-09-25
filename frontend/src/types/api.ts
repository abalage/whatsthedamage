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
  metadata?: unknown | null;
}

/**
 * Shape used by the pivot store to hold transaction data grouped by
 * account, category, and month. Built client-side in PivotTable from
 * the /api/v2/transactions endpoint.
 */
export interface ResultsApiResponse {
  accounts: Account[];
  highlights: StatisticalHighlights;
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
  result_id: string | null;
  account?: string;
  category_id?: string;
  month?: string;
  group_by: string;
  groups: Record<string, TransactionListItem[]>;
  highlights: Record<string, string[]>;
  total_count: number;
}

