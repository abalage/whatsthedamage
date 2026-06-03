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
interface DisplayRawField {
  display: string;
  raw: number | string;
}

/**
 * Date with display format and timestamp
 */
interface DateField {
  display: string;
  timestamp: number;
}



// ============================================================================
// Data Models (from dt_models.py)
// ============================================================================

/**
 * A single detailed transaction row
 */
interface DetailRow {
  row_id: string;
  date: DateField;
  amount: DisplayRawField;
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
export interface AggregatedRow {
  row_id: string;
  category: string;
  total: DisplayRawField;
  date: DateField;
  details: DetailRow[];
  is_calculated?: boolean;
}

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
 * Account data structure for results
 */
export interface AccountData {
  id: string;
  formatted_id: string;
  currency: string;
  transactions: TransactionData[];
  summary: AccountSummary;
}

/**
 * Individual transaction data
 */
interface TransactionData {
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
interface AccountSummary {
  total_transactions: number;
  total_amount: number;
  categories: CategorySummary[];
}

/**
 * Category-level summary
 */
interface CategorySummary {
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
export interface ProcessApiResponse {
  data: AggregatedRow[];
  metadata: ProcessingMetadata;
}

// -----------------------------------------------------------------------------
// Results Endpoint: GET /api/v2/results/<result_id>
// -----------------------------------------------------------------------------

/**
 * Data for a single account in results response
 */
export interface AccountDataResponse {
  id: string;
  name: string;
  dt_response: {
    data: AggregatedRow[];
  };
}

/**
 * Container for all accounts data
 */
interface AccountsDataResponse {
  accounts: AccountDataResponse[];
  highlights: StatisticalHighlights;
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

/**
 * Response from GET /api/v2/results/<result_id>
 *
 * Contains cached processing results with accounts data and drilldown URLs.
 */
export interface ResultsApiResponse {
  result_id: string;
  accounts_data: AccountsDataResponse;
  drilldown_urls_by_account: Record<string, DrilldownUrls>;
}

/**
 * Container for all accounts data
 */
interface AccountsDataResponse {
  accounts: AccountDataResponse[];
  highlights: StatisticalHighlights;
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
// Drilldown Endpoints
// -----------------------------------------------------------------------------

/**
 * Data for a single month in category months response
 */
export interface MonthData {
  month: string;
  month_timestamp: number;
  total: DisplayRawField;
  row_id: string;
  cell_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months
 *
 * Returns month-by-month aggregation for a specific category.
 */
export interface CategoryMonthsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  category_id: string;
  category_name: string;
  data: MonthData[];
  highlights?: StatisticalHighlights;
}

/**
 * Data for a single category in month categories response
 */
export interface CategoryData {
  category: string;
  total: DisplayRawField;
  row_id: string;
  category_url: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/months/<m>/categories
 *
 * Returns category-by-category aggregation for a specific month.
 */
export interface MonthCategoriesApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  month_id: string;
  month_name: string;
  data: CategoryData[];
  highlights?: StatisticalHighlights;
}

/**
 * Data for a single transaction in drilldown response
 */
interface TransactionDetailResponse {
  date: { display: string };
  amount: DisplayRawField;
  merchant: string;
  row_id: string;
}

/**
 * Response from GET /api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions
 *
 * Returns individual transaction details for a specific category and month.
 */
export interface CategoryMonthTransactionsApiResponse {
  result_id: string;
  account_id: string;
  account_name: string;
  category_id: string;
  category_name: string;
  month_id: string;
  month_name: string;
  data: TransactionDetailResponse[];
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

