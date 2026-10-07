/**
 * Composable for building navigation queries carrying the optional resultId filter
 * @module composables/useResultQuery
 */

import { useRoute } from 'vue-router'
import { buildResultQuery, extractResultId } from '../js/routeUtils.js'

/**
 * Creates a function that builds a location query carrying the current
 * optional resultId filter read from the route's query string
 * @returns Function returning the query object for router navigation
 */
export function useResultQuery(): () => { resultId?: string } {
  const route = useRoute()
  return () => buildResultQuery(extractResultId(route.query as Record<string, unknown>))
}
