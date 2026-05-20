/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError, ApiResponse } from '../types';
import {
  // Legacy type aliases for backward compatibility
  ProcessResponse,
  ResultsResponseV2,
  AccountResultsResponse,
  CategoryMonthsResponse,
  MonthCategoriesResponse,
  CategoryMonthTransactionsResponse,
} from '../types/api';

// API base URL configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v2';

/**
 * Fetch with proper error handling and response wrapping
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns Promise with wrapped API response
 */
export async function fetchApi<T>(
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
export async function fetchWithErrorHandling<T>(
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
export async function postData<T>(
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
export function getApiUrl(endpoint: string): string {
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
export async function processTransactions(formData: FormData): Promise<ProcessResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary for multipart
    });

    if (!response.ok) {
      let errorMessage = 'Transaction processing failed'
      try {
        const errorData: Record<string, unknown> = await response.json()
        errorMessage = (errorData.error ?? errorData.message ?? errorData.detail ?? errorMessage) as string
      } catch (/* jsonError */ _error: unknown) { // eslint-disable-line @typescript-eslint/no-unused-vars
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
): Promise<Record<string, unknown>> {
  return postData(`${API_BASE_URL}/recalculate-statistics`, {
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
export async function fetchResults(resultId: string): Promise<ResultsResponseV2> {
  return fetchWithErrorHandling<ResultsResponseV2>(getApiUrl(`/results/${resultId}`));
}

/**
 * Fetch account results data (for details page)
 * @param resultId - Result ID
 * @returns Promise with account results data
 */
export async function fetchAccountResults(resultId: string): Promise<AccountResultsResponse> {
  return fetchWithErrorHandling<AccountResultsResponse>(getApiUrl(`/results/${resultId}`));
}

/**
 * Fetch category months data (drilldown)
 * @param params - Route parameters containing resultId, accountId, categoryId
 * @returns Promise with category months data
 */
export async function fetchCategoryMonths(
  params: Record<string, string | null>
): Promise<CategoryMonthsResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const categoryId = params.categoryId ?? ''
  return fetchWithErrorHandling<CategoryMonthsResponse>(
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
): Promise<MonthCategoriesResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const monthId = params.monthId ?? ''
  return fetchWithErrorHandling<MonthCategoriesResponse>(
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
): Promise<CategoryMonthTransactionsResponse> {
  const resultId = params.resultId ?? ''
  const accountId = params.accountId ?? ''
  const categoryId = params.categoryId ?? ''
  const monthId = params.monthId ?? ''
  return fetchWithErrorHandling<CategoryMonthTransactionsResponse>(
    getApiUrl(`/results/${resultId}/accounts/${accountId}/categories/${categoryId}/months/${monthId}/transactions`)
  );
}