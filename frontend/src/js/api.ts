/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError, ApiResponse } from '../types/index.js';
import type {
  DetailedResponse,
  ResultsApiResponse,
  CategoryMonthsApiResponse,
  MonthCategoriesApiResponse,
  CategoryMonthTransactionsApiResponse,
  RecalculateApiResponse,
  CategoryDefinition,
  CsvProfile,
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
  return fetchWithErrorHandling<T>(url, {
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
 * Process transactions via API
 * Note: This uses direct fetch (not fetchWithErrorHandling) because:
 * 1. It's a multipart form upload (FormData)
 * 2. Content-Type must be set by the browser with boundary
 * 3. We need to handle the response differently (no JSON in body for multipart)
 *
 * @param formData - Form data containing CSV and config files
 * @returns Promise with processing result
 * @throws AppError if processing fails
 */
export async function processTransactions(formData: FormData): Promise<DetailedResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
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
 * @param resultId - Result ID
 * @param algorithms - Algorithms to use
 * @param direction - Direction (columns/rows)
 * @returns Promise with statistics result
 */
export async function recalculateStatistics(
  resultId: string,
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
 * Fetch results data
 * @param resultId - Result ID
 * @returns Promise with results data
 */
export async function fetchResults(resultId: string): Promise<ResultsApiResponse> {
  return fetchWithErrorHandling<ResultsApiResponse>(getApiUrl(`/results/${resultId}`));
}

/**
 * Fetch category months data (drilldown)
 * @param params - Route parameters containing resultId, accountId, categoryId
 * @returns Promise with category months data
 */
export async function fetchCategoryMonths(
  params: Record<string, string | null>
): Promise<CategoryMonthsApiResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const categoryId = params.categoryId ?? ''
  return fetchWithErrorHandling<CategoryMonthsApiResponse>(
    getApiUrl(`/results/${resultId}/accounts/${accountId}/categories/${categoryId}/months`)
  );
}

/**
 * Fetch month categories data (drilldown)
 * @param params - Route parameters containing resultId, accountId, monthId
 * @returns Promise with month categories data
 */
export async function fetchMonthCategories(
  params: Record<string, string | null>
): Promise<MonthCategoriesApiResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const monthId = params.monthId ?? ''
  return fetchWithErrorHandling<MonthCategoriesApiResponse>(
    getApiUrl(`/results/${resultId}/accounts/${accountId}/months/${monthId}/categories`)
  );
}

/**
 * Fetch category month transactions data (drilldown)
 * @param params - Route parameters containing resultId, accountId, categoryId, monthId
 * @returns Promise with category month transactions data
 */
export async function fetchCategoryMonthTransactions(
  params: Record<string, string | null>
): Promise<CategoryMonthTransactionsApiResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const categoryId = params.categoryId ?? ''
  const monthId = params.monthId ?? ''
  return fetchWithErrorHandling<CategoryMonthTransactionsApiResponse>(
    getApiUrl(`/results/${resultId}/accounts/${accountId}/categories/${categoryId}/months/${monthId}/transactions`)
  );
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
  console.log('Fetching cost of living categories...');
  return fetchWithErrorHandling<CategoryDefinition[]>(getApiUrl('/categories/cost-of-living'));
}

/**
 * Fetch all CSV profiles
 * @returns Promise with array of CsvProfile objects
 */
export async function fetchAllCsvProfiles(): Promise<CsvProfile[]> {
  return fetchWithErrorHandling<CsvProfile[]>(getApiUrl('/csv-profiles'));
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
 * Get a new CSRF token
 * @returns Promise with CSRF token
 */
async function getCsrfToken(): Promise<CsrfTokenResponse> {
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
 * Fetch with automatic CSRF token inclusion for state-changing requests
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns Promise with parsed data
 */
async function fetchWithCsrf<T>(
  url: string,
  options: RequestInit = {}
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
    
    return fetchWithErrorHandling<T>(url, {
      ...options,
      credentials: 'include',
      headers
    });
  }
  
  // For non-state-changing requests, just use credentials
  return fetchWithCredentials<T>(url, options);
}

