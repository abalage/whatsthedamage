/**
 * Route-related utility functions
 * @module utils/routeUtils
 */

/**
 * Build a location query carrying an optional resultId filter
 * @param resultId - Result ID to filter by, or null/undefined for all transactions
 * @returns Query object for router navigation (empty when unfiltered)
 */
export function buildResultQuery(resultId: string | null | undefined): { resultId?: string } {
  return resultId ? { resultId } : {}
}

/**
 * Extract an optional resultId from route query or params
 * @param source - Object containing route query or params values
 * @returns Result ID string, or null when absent
 */
export function extractResultId(source: Record<string, unknown>): string | null {
  const value = source.resultId
  if (typeof value === 'string' && value !== '') {
    return value
  }
  if (Array.isArray(value) && typeof value[0] === 'string' && value[0] !== '') {
    return value[0]
  }
  return null
}
