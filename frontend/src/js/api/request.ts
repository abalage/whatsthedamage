/**
 * Shared transport for all API requests: header construction, CSRF
 * token handling, and error parsing. The domain modules (auth,
 * transactions, processing) build their endpoints on top of request().
 * @module utils/api/request
 */

import { AppError, type ApiErrorBody } from '../../types/index'
import { getCsrfToken } from '../csrfToken'

// API base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v2'

/**
 * State-changing HTTP methods that require CSRF protection
 */
const CSRF_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH'])

/**
 * Build the request headers: JSON content type unless the body is
 * multipart (the browser sets the Content-Type with boundary), merged
 * with any caller-provided headers, plus the CSRF token for
 * state-changing methods.
 * @param options - Fetch options
 * @returns Complete header map for the request
 */
function buildHeaders(options: RequestInit): Record<string, string> {
  const headers: Record<string, string> = {}
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value
      })
    } else if (Array.isArray(options.headers)) {
      for (const [key, value] of options.headers) {
        headers[key] = value
      }
    } else {
      Object.assign(headers, options.headers)
    }
  }
  const method = options.method?.toUpperCase() ?? 'GET'
  if (CSRF_METHODS.has(method)) {
    const token = getCsrfToken()
    if (token) {
      headers['X-CSRF-Token'] = token
    }
  }
  return headers
}

/**
 * Parsed fields of an error response body
 */
interface ParsedApiError {
  /** Human-readable error message */
  message: string
  /** Machine-readable error code, when the backend provides one */
  code?: string
}

/**
 * Extract the error message and code from an error response body.
 * @param response - Non-OK fetch response
 * @returns Promise with the parsed message and optional code
 */
async function parseApiError(response: Response): Promise<ParsedApiError> {
  let message = response.statusText || 'Request failed'
  let code: string | undefined
  try {
    const errorData = await response.json() as ApiErrorBody
    const extracted = errorData.error ?? errorData.message ?? errorData.detail
    if (typeof extracted === 'string') {
      message = extracted
    }
    if (typeof errorData.code === 'string') {
      code = errorData.code
    }
  } catch {
    // No JSON body; keep the status text fallback
  }
  return { message, code }
}

/**
 * Whether an error response is a rejected CSRF token (the sent token
 * no longer matches the hash stored for the session)
 * @param status - HTTP status of the response
 * @param code - Machine-readable error code from the response body
 * @returns Whether the failure is an invalid CSRF token
 */
function isInvalidCsrfTokenError(status: number, code: string | undefined): boolean {
  return status === 403 && code === 'CSRF_TOKEN_INVALID'
}

/**
 * Mint a fresh CSRF token from the backend. The backend sets the
 * token as a cookie; the new value is read back from it.
 * @returns The new CSRF token, or null when the refresh failed
 */
async function refreshCsrfToken(): Promise<string | null> {
  try {
    await request(getApiUrl('/auth/csrf-token'))
    return getCsrfToken() ?? null
  } catch {
    return null
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
export async function request<T>(
  url: string,
  options: RequestInit = {},
  allowCsrfRetry = true
): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: buildHeaders(options)
    })
  } catch (error: unknown) {
    throw new AppError(
      `API request failed: ${error instanceof Error ? error.message : String(error)}`,
      { url, options }
    )
  }

  if (!response.ok) {
    const { message, code } = await parseApiError(response)
    if (allowCsrfRetry && isInvalidCsrfTokenError(response.status, code)) {
      const refreshedToken = await refreshCsrfToken()
      if (refreshedToken) {
        return request<T>(url, options, false)
      }
    }
    throw new AppError(message, { status: response.status, url })
  }

  return (await response.json()) as T
}

/**
 * POST request with a JSON body
 * @param url - API endpoint URL
 * @param data - Request body
 * @returns Promise with parsed data
 */
export async function postData<T>(
  url: string,
  data: unknown
): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get full API URL
 * @param endpoint - API endpoint path
 * @returns Full API URL
 */
export function getApiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`
}

/**
 * API base URL, used by modules building raw multipart URLs
 */
export { API_BASE_URL }
