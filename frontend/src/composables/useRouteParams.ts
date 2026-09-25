/**
 * Composable for extracting and type-safe route parameters
 * @module composables/useRouteParams
 */

import { computed, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { extractResultId } from '../js/routeUtils.js'

/**
 * String-only route parameters type
 */
export type StringRouteParams = Record<string, string | null>

/**
 * Extracts common route parameters with type safety
 * The resultId is read from route params first, then from the query string,
 * so both path-based and query-based result filtering are supported
 * @returns Object with computed refs for resultId, accountId, categoryId, and monthId
 */
export function useRouteParams(): {
  resultId: ComputedRef<string | null>
  accountId: ComputedRef<string | null>
  categoryId: ComputedRef<string | null>
  monthId: ComputedRef<string | null>
  stringParams: ComputedRef<StringRouteParams>
  convertParamsToString: (params: Record<string, string | string[] | null>) => StringRouteParams
} {
  const route = useRoute()

  const resultId = computed(() => {
    const paramId = extractResultId(route.params as Record<string, unknown>)
    return paramId ?? extractResultId(route.query as Record<string, unknown>)
  })

  const accountId = computed(() => {
    const value = route.params.accountId
    return typeof value === 'string' ? value : null
  })

  const categoryId = computed(() => {
    const value = route.params.categoryId
    return typeof value === 'string' ? value : null
  })

  const monthId = computed(() => {
    const value = route.params.monthId
    return typeof value === 'string' ? value : null
  })

  /**
   * Converts RouteParams (which may contain string arrays) to StringRouteParams
   */
  const convertParamsToString = (params: Record<string, string | string[] | null>): StringRouteParams => {
    const stringParams: StringRouteParams = {}
    for (const [key, value] of Object.entries(params)) {
      if (value === null) {
        stringParams[key] = null
      } else if (Array.isArray(value)) {
        stringParams[key] = value.length > 0 ? value[0] : null
      } else if (typeof value === 'string') {
        stringParams[key] = value
      } else {
        stringParams[key] = null
      }
    }
    return stringParams
  }

  /**
   * Gets all route params as StringRouteParams, including the resultId
   * from either path params or the query string
   */
  const stringParams = computed<StringRouteParams>(() => {
    const params = convertParamsToString(route.params)
    params.resultId ??= resultId.value
    return params
  })

  return {
    resultId,
    accountId,
    categoryId,
    monthId,
    stringParams,
    convertParamsToString
  }
}
