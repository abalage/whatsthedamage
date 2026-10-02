/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError, ApiResponse } from '../types/index.js';
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
} from '../types/auth.js';

// API base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v2';

/**
 * Fetch with proper error handling and response wrapping
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns Promise with wrapped API response
 */
async function fetchApi<T>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data: T = await response.json();

    return {
      data,
      status: response.status,
      ok: response.ok,
      error: response.ok ? undefined : ((data as Record<string, unknown>)?.error as string | undefined) ?? 'Request failed',
    };
  } catch (error) {
    throw new AppError(
      `API request failed: ${error instanceof Error ? error.message : String(error)}`,
      { url, options }
    );
  }
}

/**
 * Fetch with automatic error handling
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns Promise with parsed data
 * @throws AppError if request fails
 */
async function fetchWithErrorHandling<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetchApi<T>(url, options);

  if (!response.ok) {
    throw new AppError(response.error ?? 'Request failed', {
      status: response.status,
      url,
    });
  }

  return response.data;
}

/**
 * POST request with error handling
 * @param url - API endpoint URL
 * @param data - Request body
 * @returns Promise with parsed data
 */
async function postData<T>(
  url: string,
  data: unknown
): Promise<T> {
  return fetchWithCsrf<T>(url, {
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
 * Process transactions via API (new RESTful endpoint)
 * Note: This uses direct fetch (not fetchWithErrorHandling) because:
 * 1. It's a multipart form upload (FormData)
 * 2. Content-Type must be set by the browser with boundary
 * 3. We need to handle the response differently (no JSON in body for multipart)
 *
 * @param formData - Form data containing CSV and config files
 * @returns Promise with processing result metadata (flat structure)
 * @throws AppError if processing fails
 */
export async function createTransaction(formData: FormData): Promise<ProcessingResultCreationResponse> {
  try {
    // Get CSRF token from store for state-changing POST request
    const csrfToken = await getCsrfTokenFromStore();

    // Build headers manually - let browser set Content-Type for multipart
    const headers: Record<string, string> = {};
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const response = await fetch(`${API_BASE_URL}/processing-results`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers,
      // Don't set Content-Type header - let browser set it with boundary for multipart
    });

    if (!response.ok) {
      let errorMessage = 'Transaction processing failed'
      try {
        const errorData: Record<string, unknown> = await response.json()
        errorMessage = (errorData.error ?? errorData.message ?? errorData.detail ?? errorMessage) as string
      } catch {
        // If we can't parse JSON, use the status text
        errorMessage = response.statusText || errorMessage
      }
      throw new AppError(errorMessage, {
        status: response.status,
      })
    }

    return await response.json()
  } catch (error: unknown) {
    if (error instanceof AppError) {
      throw error
    }
    throw new AppError(
      `Transaction processing failed: ${error instanceof Error ? error.message : String(error)}`,
      { originalError: error }
    )
  }
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
  return fetchWithErrorHandling<CategoryDefinition[]>(getApiUrl('/categories'));
}

/**
 * Fetch cost of living category definition
 * @returns Promise with array of CategoryDefinition objects
 */
export async function fetchCostOfLivingCategories(): Promise<CategoryDefinition[]> {
  return fetchWithErrorHandling<CategoryDefinition[]>(getApiUrl('/categories/cost-of-living'));
}

/**
 * Fetch all CSV profiles
 * @returns Promise with array of CsvProfile objects
 */
export async function fetchAllCsvProfiles(): Promise<CsvProfile[]> {
  return fetchWithErrorHandling<CsvProfile[]>(getApiUrl('/csv-profiles'));
}

/**
 * Fetch all processing results for the authenticated user
 * @returns Promise with array of ProcessingResultListItem objects
 */
export async function fetchProcessingResults(): Promise<ProcessingResultListItem[]> {
  return fetchWithErrorHandling<ProcessingResultListItem[]>(getApiUrl('/processing-results'), {
    credentials: 'include'
  });
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
  return fetchWithErrorHandling<ProcessingResultMetadata>(getApiUrl(`/processing-results/${encodeURIComponent(resultId)}`), {
    credentials: 'include'
  });
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

  return fetchWithErrorHandling<TransactionListResponse>(
    getApiUrl(query ? `/transactions?${query}` : '/transactions'),
    { credentials: 'include' }
  );
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
  return fetchWithCsrf<TransactionListItem>(getApiUrl(`/transactions/${id}`), {
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
  return fetchWithCsrf<TransactionListItem>(getApiUrl(`/transactions/${id}/undo`), {
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

  return fetchWithErrorHandling<AggregatedTransactionsResponse>(
    getApiUrl(`/transactions/aggregate?${searchParams.toString()}`),
    { credentials: 'include' }
  );
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
  return fetchWithCsrf<RegisterResponse>(getApiUrl('/auth/register'), {
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
  return fetchWithCsrf<LoginResponse>(getApiUrl('/auth/login'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  });
}

/**
 * Logout the current user
 * @returns Promise with logout response
 */
export async function logout(): Promise<LogoutResponse> {
  return fetchWithCsrf<LogoutResponse>(getApiUrl('/auth/logout'), {
    method: 'POST',
    body: JSON.stringify({})
  });
}

/**
 * Get current user information and CSRF token
 * @returns Promise with user info and CSRF token
 */
export async function getMe(): Promise<MeResponse> {
  return fetchWithErrorHandling<MeResponse>(getApiUrl('/auth/me'), {
    credentials: 'include'
  });
}

/**
 * Update the current user's correction sharing opt-in preference
 * @param optIn - Whether the user opts in to sharing corrections
 * @returns Promise with the updated user
 */
export async function updateSharingPreference(optIn: boolean): Promise<UpdateMeResponse> {
  const requestData: UpdateMeRequest = { opt_in_sharing: optIn };
  return fetchWithCsrf<UpdateMeResponse>(getApiUrl('/auth/me'), {
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
  return fetchWithErrorHandling<CsrfTokenResponse>(getApiUrl('/auth/csrf-token'), {
    credentials: 'include'
  });
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
  return fetchWithCsrf<PasswordResetResponse>(getApiUrl('/auth/reset-password'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  });
}

/**
 * Fetch with automatic inclusion of credentials (cookies)
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns Promise with parsed data
 */
async function fetchWithCredentials<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  return fetchWithErrorHandling<T>(url, {
    ...options,
    credentials: 'include'
  });
}

/**
 * State-changing HTTP methods that require CSRF protection
 */
const CSRF_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

/**
 * Get CSRF token from auth store
 * @returns CSRF token string or null
 */
async function getCsrfTokenFromStore(): Promise<string | null> {
  try {
    // Import dynamically to avoid circular dependencies
    const { useAuthStore } = await import('../stores/auth.js');
    const authStore = useAuthStore();
    return authStore.getCsrfToken?.() ?? null;
  } catch {
    return null;
  }
}

/**
 * Mint a fresh CSRF token via the auth store so every consumer sees it
 * @returns The new CSRF token, or null when the refresh failed
 */
async function refreshCsrfTokenViaStore(): Promise<string | null> {
  try {
    const { useAuthStore } = await import('../stores/auth.js');
    const authStore = useAuthStore();
    await authStore.refreshCsrfToken();
    return authStore.getCsrfToken?.() ?? null;
  } catch {
    return null;
  }
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
 * Fetch with automatic CSRF token inclusion for state-changing requests.
 * When the server rejects the token as invalid (e.g. it was superseded by
 * a token minted in another tab), a fresh token is minted and the request
 * is retried once.
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param allowCsrfRetry - Whether a rejected CSRF token may be retried
 * @returns Promise with parsed data
 */
async function fetchWithCsrf<T>(
  url: string,
  options: RequestInit = {},
  allowCsrfRetry = true
): Promise<T> {
  // Only add CSRF token for state-changing methods
  const method = (options.method?.toUpperCase() ?? 'GET');

  if (CSRF_METHODS.has(method)) {
    const csrfToken = await getCsrfTokenFromStore();

    // Build headers - only include CSRF token if available
    // This allows auth endpoints (register/login) to work without CSRF
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Safely merge headers from options
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

    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    try {
      return await fetchWithErrorHandling<T>(url, {
        ...options,
        credentials: 'include',
        headers
      });
    } catch (error) {
      if (allowCsrfRetry && isInvalidCsrfTokenError(error)) {
        const refreshedToken = await refreshCsrfTokenViaStore();
        if (refreshedToken) {
          return fetchWithCsrf<T>(url, options, false);
        }
      }
      throw error;
    }
  }

  // For non-state-changing requests, just use credentials
  return fetchWithCredentials<T>(url, options);
}

