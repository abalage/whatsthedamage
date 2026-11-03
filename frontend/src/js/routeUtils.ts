/**
 * Route-related utility functions
 * @module utils/routeUtils
 */

/**
 * Build a location query carrying an optional resultId filter
 * @param resultId - Result ID to filter by, or undefined for all transactions
 * @returns Query object for router navigation (empty when unfiltered)
 */
export function buildResultQuery(resultId: string | undefined): { resultId?: string } {
  return resultId ? { resultId } : {}
}

/**
 * Extract an optional resultId from the route query
 * @param source - Object containing route query values
 * @returns Result ID string, or undefined when absent
 */
export function extractResultId(source: Record<string, unknown>): string | undefined {
  const value = source.resultId
  if (typeof value === 'string' && value !== '') {
    return value
  }
  if (Array.isArray(value) && typeof value[0] === 'string' && value[0] !== '') {
    return value[0]
  }
  return undefined
}

/**
 * Extract a safe in-app redirect target from a route query.
 * Only same-app paths (starting with a single "/") are accepted;
 * external URLs and protocol-relative URLs are rejected.
 * @param source - Object containing route query values
 * @returns The redirect path, or undefined when absent or unsafe
 */
export function safeRedirectParam(source: Record<string, unknown>): string | undefined {
  const value = source.redirect
  if (typeof value !== 'string' || value === '') {
    return undefined
  }
  if (!value.startsWith('/') || value.startsWith('//')) {
    return undefined
  }
  return value
}

/**
 * Build a location query carrying an optional redirect target
 * @param redirect - Redirect path (see safeRedirectParam), or undefined
 * @returns Query object for router navigation (empty when no redirect)
 */
export function buildRedirectQuery(redirect: string | undefined): { redirect?: string } {
  return redirect ? { redirect } : {}
}
