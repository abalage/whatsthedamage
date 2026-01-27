/**
 * API utility functions for What's the Damage frontend
 * @module utils/api
 */

import { AppError, ApiResponse } from '../types';

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