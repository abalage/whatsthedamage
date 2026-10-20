/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError } from '../types/index.js';
import { getCsrfToken, setCsrfToken } from './csrfToken.js';
import type {
  AggregatedTransactionsResponse,
  CategoryDefinition,
  CsvProfile,
  ProcessingResultCreationResponse,
  ProcessingResultListItem,
  ProcessingResultMetadata,
  RecalculateApiResponse,
  TransactionListItem,
  TransactionListResponse,
  TransactionUpdatePayload,
} from '../types/api.js';
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MeResponse,
  CsrfTokenResponse,
  PasswordResetRequest,
  PasswordResetResponse,
  UpdateMeRequest,
  UpdateMeResponse,
  AccountDeletionRequest,
  AccountDeletionResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  DataExportResponse,
} from '../types/auth.js';

// API base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v2';

/**
 * State-changing HTTP methods that require CSRF protection
 */
const CSRF_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

/**
 * Build the request headers: JSON content type unless the body is
 * multipart (the browser sets the Content-Type with boundary), merged
 * with any caller-provided headers, plus the CSRF token for
 * state-changing methods.
 * @param options - Fetch options
 * @returns Complete header map for the request
 */
function buildHeaders(options: RequestInit): Record<string, string> {
  const headers: Record<string, string> = {};
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(options.headers)) {
      for (const [key, value] of options.headers) {
        headers[key] = value;
      }
    } else {
      Object.assign(headers, options.headers);
    }
  }
  const method = options.method?.toUpperCase() ?? 'GET';
  if (CSRF_METHODS.has(method)) {
    const token = getCsrfToken();
    if (token) {
      headers['X-CSRF-Token'] = token;
    }
  }
  return headers;
}

/**
 * Extract the error message from an error response body.
 * @param response - Non-OK fetch response
 * @returns Promise with the error message
 */
async function parseApiError(response: Response): Promise<string> {
  let message = response.statusText || 'Request failed';
  try {
    const errorData: Record<string, unknown> = await response.json();
    const extracted = errorData.error ?? errorData.message ?? errorData.detail;
    if (typeof extracted === 'string') {
      message = extracted;
    }
  } catch {
    // No JSON body; keep the status text fallback
  }
  return message;
}

/**
 * Whether an error is a rejected CSRF token (the sent token no longer
 * matches the hash stored for the session)
 */
function isInvalidCsrfTokenError(error: unknown): boolean {
  if (!(error instanceof AppError)) return false;
  const context = error.context as { status?: number } | undefined;
  return context?.status === 403 && /invalid csrf token/i.test(error.message);
}

/**
 * Mint a fresh CSRF token from the backend and store it for the next
 * state-changing request.
 * @returns The new CSRF token, or null when the refresh failed
 */
async function refreshCsrfToken(): Promise<string | null> {
  try {
    const response = await request<CsrfTokenResponse>(getApiUrl('/auth/csrf-token'));
    setCsrfToken(response.csrf_token);
    return response.csrf_token;
  } catch {
    return null;
  }
}

/**
 * Single transport for all API requests. Always sends cookies
 * (credentials), attaches the CSRF token to state-changing methods,
 * and retries a rejected token once with a freshly minted one.
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param allowCsrfRetry - Whether a rejected CSRF token may be retried
 * @returns Promise with parsed data
 * @throws AppError if the request fails
 */
async function request<T>(
  url: string,
  options: RequestInit = {},
  allowCsrfRetry = true
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: buildHeaders(options)
    });
  } catch (error: unknown) {
    throw new AppError(
      `API request failed: ${error instanceof Error ? error.message : String(error)}`,
      { url, options }
    );
  }

  if (!response.ok) {
    const message = await parseApiError(response);
    if (allowCsrfRetry && isInvalidCsrfTokenError(new AppError(message, { status: response.status }))) {
      const refreshedToken = await refreshCsrfToken();
      if (refreshedToken) {
        return request<T>(url, options, false);
      }
    }
    throw new AppError(message, { status: response.status, url });
  }

  return (await response.json()) as T;
}

/**
 * POST request with a JSON body
 * @param url - API endpoint URL
 * @param data - Request body
 * @returns Promise with parsed data
 */
async function postData<T>(
  url: string,
  data: unknown
): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get full API URL
 * @param endpoint - API endpoint path
 * @returns Full API URL
 */
function getApiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`;
}

/**
 * Process transactions via API (multipart form upload; the browser
 * sets the Content-Type with boundary)
 *
 * @param formData - Form data containing CSV and config files
 * @returns Promise with processing result metadata (flat structure)
 * @throws AppError if processing fails
 */
export async function createTransaction(formData: FormData): Promise<ProcessingResultCreationResponse> {
  // The body is multipart; request() lets the browser set the
  // Content-Type with boundary and attaches the CSRF token
  return request<ProcessingResultCreationResponse>(
    `${API_BASE_URL}/processing-results`,
    { method: 'POST', body: formData }
  );
}

/**
 * Recalculate statistics
 * @param resultId - Result ID, or undefined to use all of the user's transactions
 * @param algorithms - Algorithms to use
 * @param direction - Direction (columns/rows)
 * @returns Promise with statistics result
 */
export async function recalculateStatistics(
  resultId: string | undefined,
  algorithms: string[],
  direction: 'columns' | 'rows'
): Promise<RecalculateApiResponse> {
  return postData<RecalculateApiResponse>(`${API_BASE_URL}/recalculate-statistics`, {
    result_id: resultId,
    algorithms,
    direction,
  });
}

/**
 * Fetch month categories data (drilldown)
 * @param params - Route parameters containing resultId, accountId, monthId
 * @param options - Statistical analysis options (algorithms, direction)
 * @returns Promise with aggregated transactions data
 */
export async function fetchMonthCategories(
  params: Record<string, string | null>,
  options: StatisticalAnalysisOptions = {}
): Promise<AggregatedTransactionsResponse> {
  return fetchAggregatedTransactions({
    result_id: params.resultId ?? undefined,
    account: params.accountId ?? undefined,
    month: params.monthId ?? undefined,
    group_by: 'category',
    ...options
  });
}

/**
 * Fetch category month transactions data (drilldown)
 * @param params - Route parameters containing resultId, accountId, categoryId, monthId
 * @returns Promise with transaction list data
 */
export async function fetchCategoryMonthTransactions(
  params: Record<string, string | null>
): Promise<TransactionListResponse> {
  return fetchAllTransactions(params.resultId ?? undefined, {
    account: params.accountId ?? undefined,
    categoryId: params.categoryId ?? undefined,
    month: params.monthId ?? undefined
  });
}

/**
 * Fetch all category definitions
 * @returns Promise with array of CategoryDefinition objects
 */
export async function fetchCategories(): Promise<CategoryDefinition[]> {
  return request<CategoryDefinition[]>(getApiUrl('/categories'));
}

/**
 * Fetch cost of living category definition
 * @returns Promise with array of CategoryDefinition objects
 */
export async function fetchCostOfLivingCategories(): Promise<CategoryDefinition[]> {
  return request<CategoryDefinition[]>(getApiUrl('/categories/cost-of-living'));
}

/**
 * Fetch all CSV profiles
 * @returns Promise with array of CsvProfile objects
 */
export async function fetchAllCsvProfiles(): Promise<CsvProfile[]> {
  return request<CsvProfile[]>(getApiUrl('/csv-profiles'));
}

/**
 * Fetch all processing results for the authenticated user
 * @returns Promise with array of ProcessingResultListItem objects
 */
export async function fetchProcessingResults(): Promise<ProcessingResultListItem[]> {
  return request<ProcessingResultListItem[]>(getApiUrl('/processing-results'));
}

/**
 * Fetch processing result metadata
 * @param resultId - Result ID, or undefined to skip the lookup
 * @returns Promise with ProcessingResultMetadata, or null when no resultId is given
 */
export async function fetchProcessingResultMetadata(resultId?: string): Promise<ProcessingResultMetadata | null> {
  if (!resultId) {
    return null
  }
  return request<ProcessingResultMetadata>(getApiUrl(`/processing-results/${encodeURIComponent(resultId)}`));
}

/**
 * Fetch transactions, optionally limited to a specific processing result
 * @param resultId - Result ID, or undefined to fetch transactions across all results
 * @param options - Filter and pagination options
 * @returns Promise with TransactionListResponse
 */
export async function fetchTransactionsByResult(
  resultId?: string,
  options: {
    limit?: number;
    offset?: number;
    account?: string;
    categoryId?: string;
    month?: string;
    sortBy?: string;
    sortOrder?: string;
  } = {}
): Promise<TransactionListResponse> {
  const params = new URLSearchParams();
  if (resultId) params.append('result_id', resultId);
  if (options.limit !== undefined) params.append('limit', options.limit.toString());
  if (options.offset !== undefined) params.append('offset', options.offset.toString());
  if (options.account) params.append('account', options.account);
  if (options.categoryId) params.append('category_id', options.categoryId);
  if (options.month) params.append('month', options.month);
  if (options.sortBy) params.append('sort_by', options.sortBy);
  if (options.sortOrder) params.append('sort_order', options.sortOrder);

  const query = params.toString();

  return request<TransactionListResponse>(
    getApiUrl(query ? `/transactions?${query}` : '/transactions'));
}

/**
 * Page size used when fetching the complete dataset with paginated requests
 */
const TRANSACTION_PAGE_SIZE = 2000;

/**
 * Safety cap for fetch-all queries; the transaction views show a truncation
 * warning when a dataset reaches this size
 */
const MAX_FETCHED_TRANSACTIONS = 50000;

/**
 * Fetch the complete transaction dataset, optionally limited to a specific
 * processing result, by paging through the transactions endpoint until
 * total_count rows are collected (or MAX_FETCHED_TRANSACTIONS is reached).
 * Intended for views that aggregate transactions client-side, where a single
 * limited request would silently drop rows.
 * @param resultId - Result ID, or undefined to fetch transactions across all results
 * @param options - Filter options (sorting applies to every page request)
 * @returns Promise with the complete TransactionListResponse
 */
export async function fetchAllTransactions(
  resultId?: string,
  options: {
    account?: string;
    categoryId?: string;
    month?: string;
    sortBy?: string;
    sortOrder?: string;
  } = {}
): Promise<TransactionListResponse> {
  const firstPage = await fetchTransactionsByResult(resultId, {
    ...options,
    limit: TRANSACTION_PAGE_SIZE,
    offset: 0
  });

  const transactions = [...firstPage.transactions];
  const targetCount = Math.min(firstPage.total_count, MAX_FETCHED_TRANSACTIONS);

  while (transactions.length < targetCount) {
    const page = await fetchTransactionsByResult(resultId, {
      ...options,
      limit: TRANSACTION_PAGE_SIZE,
      offset: transactions.length
    });
    if (page.transactions.length === 0) {
      // The dataset shrank between requests; stop with what we have
      break;
    }
    transactions.push(...page.transactions);
  }

  return {
    transactions,
    total_count: firstPage.total_count,
    limit: transactions.length,
    offset: 0
  };
}

/**
 * Update correctable attributes (category, partner, notice) of a transaction
 * @param id - Transaction identifier
 * @param payload - Fields to correct
 * @returns Promise with the updated transaction
 */
export async function updateTransaction(
  id: number,
  payload: TransactionUpdatePayload
): Promise<TransactionListItem> {
  return request<TransactionListItem>(getApiUrl(`/transactions/${id}`), {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/**
 * Undo all corrections of a transaction, restoring the original
 * category, merchant, and notice values
 * @param id - Transaction identifier
 * @returns Promise with the restored transaction
 */
export async function undoTransaction(
  id: number
): Promise<TransactionListItem> {
  return request<TransactionListItem>(getApiUrl(`/transactions/${id}/undo`), {
    method: 'POST',
  });
}

/**
 * Statistical analysis options for aggregation and recalculation endpoints
 */
export interface StatisticalAnalysisOptions {
  algorithms?: string[];
  direction?: 'columns' | 'rows';
}

/**
 * Fetch aggregated transaction data for drilldown views
 * @param params - Aggregation parameters
 * @returns Promise with AggregatedTransactionsResponse
 */
export async function fetchAggregatedTransactions(params: {
  result_id?: string;
  account?: string;
  category_id?: string;
  month?: string;
  group_by: string;
  algorithms?: string[];
  direction?: 'columns' | 'rows';
}): Promise<AggregatedTransactionsResponse> {
  const searchParams = new URLSearchParams();
  if (params.result_id) searchParams.append('result_id', params.result_id);
  if (params.account) searchParams.append('account', params.account);
  if (params.category_id) searchParams.append('category_id', params.category_id);
  if (params.month) searchParams.append('month', params.month);
  searchParams.append('group_by', params.group_by);
  if (params.algorithms) searchParams.append('algorithms', params.algorithms.join(','));
  if (params.direction) searchParams.append('direction', params.direction);

  return request<AggregatedTransactionsResponse>(
    getApiUrl(`/transactions/aggregate?${searchParams.toString()}`));
}

// Authentication API functions

/**
 * Register a new user
 * @param username - User's username
 * @param password - User's password
 * @returns Promise with registration response
 */
export async function register(username: string, password: string): Promise<RegisterResponse> {
  const requestData: RegisterRequest = { username, password };
  return request<RegisterResponse>(getApiUrl('/auth/register'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  });
}

/**
 * Login a user
 * @param username - User's username
 * @param password - User's password
 * @param rememberMe - Whether to remember the session
 * @returns Promise with login response
 */
export async function login(username: string, password: string, rememberMe: boolean = false): Promise<LoginResponse> {
  const requestData: LoginRequest = { username, password, rememberMe };
  return request<LoginResponse>(getApiUrl('/auth/login'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  });
}

/**
 * Logout the current user
 * @returns Promise with logout response
 */
export async function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>(getApiUrl('/auth/logout'), {
    method: 'POST',
    body: JSON.stringify({})
  });
}

/**
 * Get current user information and CSRF token
 * @returns Promise with user info and CSRF token
 */
export async function getMe(): Promise<MeResponse> {
  return request<MeResponse>(getApiUrl('/auth/me'));
}

/**
 * Update the current user's correction sharing opt-in preference
 * @param optIn - Whether the user opts in to sharing corrections
 * @returns Promise with the updated user
 */
export async function updateSharingPreference(optIn: boolean): Promise<UpdateMeResponse> {
  const requestData: UpdateMeRequest = { opt_in_sharing: optIn };
  return request<UpdateMeResponse>(getApiUrl('/auth/me'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  });
}

/**
 * Get a new CSRF token
 * The backend persists the token's hash, so the returned token is valid
 * for subsequent state-changing requests (it replaces the previously
 * issued one).
 * @returns Promise with CSRF token
 */
export async function fetchCsrfToken(): Promise<CsrfTokenResponse> {
  const response = await request<CsrfTokenResponse>(getApiUrl('/auth/csrf-token'));
  setCsrfToken(response.csrf_token);
  return response;
}

/**
 * Reset password using recovery code
 * @param username - User's username
 * @param recoveryCode - Recovery code
 * @param newPassword - New password
 * @returns Promise with password reset response containing user and new recovery code
 */
export async function resetPassword(
  username: string,
  recoveryCode: string,
  newPassword: string
): Promise<PasswordResetResponse> {
  const requestData: PasswordResetRequest = {
    username,
    recoveryCode,
    newPassword
  };
  return request<PasswordResetResponse>(getApiUrl('/auth/reset-password'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  });
}

/**
 * Schedule deletion of the current user's account
 * @param password - Current password confirming the deletion request
 * @param revokeSharedCorrections - Whether to also withdraw the user's
 * shared correction contributions when the account is deleted
 * @returns Promise with the scheduled deletion timestamp
 */
export async function deleteAccount(
  password: string,
  revokeSharedCorrections: boolean = false
): Promise<AccountDeletionResponse> {
  const requestData: AccountDeletionRequest = {
    password,
    revoke_shared_corrections: revokeSharedCorrections
  };
  return request<AccountDeletionResponse>(getApiUrl('/auth/account'), {
    method: 'DELETE',
    body: JSON.stringify(requestData)
  });
}

/**
 * Change the current user's username (right to rectification)
 * @param username - New unique username
 * @returns Promise with the updated user
 */
export async function updateUsername(username: string): Promise<UpdateMeResponse> {
  const requestData: UpdateMeRequest = { username };
  return request<UpdateMeResponse>(getApiUrl('/auth/me'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  });
}

/**
 * Change the current user's password while logged in
 * @param currentPassword - Current password confirming the change
 * @param newPassword - New password (minimum 12 characters)
 * @returns Promise with a confirmation message
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<ChangePasswordResponse> {
  const requestData: ChangePasswordRequest = {
    current_password: currentPassword,
    new_password: newPassword
  };
  return request<ChangePasswordResponse>(getApiUrl('/auth/me/password'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  });
}

/**
 * Export all personal data of the current user (data portability)
 * @returns Promise with the machine-readable export document
 */
export async function exportMyData(): Promise<DataExportResponse> {
  return request<DataExportResponse>(getApiUrl('/auth/me/export'));
}
