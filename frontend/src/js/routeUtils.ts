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
