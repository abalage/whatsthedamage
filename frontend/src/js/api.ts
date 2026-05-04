/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError, ApiResponse } from '../types';

// API base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v2';

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
      error: response.ok ? undefined : (data as any)?.error || 'Request failed',
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
    throw new AppError(response.error || 'Request failed', {
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
 * @param formData - Form data containing CSV and config
 * @returns Promise with processing result
 */
export async function processTransactions(formData: FormData): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/process`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header - let browser set it with boundary for multipart
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.log('API Error Response:', errorData); // Debug log
    throw new AppError(errorData.error || errorData.message || errorData.detail || 'Transaction processing failed', {
      status: response.status,
    });
  }

  return response.json();
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
): Promise<any> {
  return postData(`${API_BASE_URL}/recalculate-statistics`, {
    result_id: resultId,
    algorithms,
    direction,
  });
}