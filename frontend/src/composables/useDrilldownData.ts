/**
 * Composable for handling drilldown page data fetching and state management
 * @module composables/useDrilldownData
 */

import { ref, computed, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { useFeedbackStore } from '../stores/feedback'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { fetchWithErrorHandling, API_BASE_URL } from '../js/api'
import type { AxiosError } from 'axios'

/**
 * Extract route parameter with type safety
 * @param param - Route parameter name
 * @returns Computed ref with string or null
 */
function useRouteParam(param: string): ComputedRef<string | null> {
  const route = useRoute()
  return computed(() => {
    const value = route.params[param]
    return typeof value === 'string' ? value : null
  })
}

/**
 * Common data fetching state
 */
interface FetchState<T> {
  data: ref<T | null>
  isLoading: ref<boolean>
  error: ref<string | null>
  fetchData: () => Promise<void>
}

/**
 * Options for creating a drilldown data fetcher
 */
interface DrilldownFetchOptions<T> {
  /**
   * Function to build the API endpoint URL from route parameters
   */
  buildEndpoint: (params: Record<string, string | null>) => string
  /**
   * Optional data transformation function
   */
  transformData?: (data: unknown) => T
}

/**
 * Creates a drilldown data fetcher with common patterns
 * @param options - Configuration options
 * @returns Fetch state and utilities
 */
export function useDrilldownData<T>(
  options: DrilldownFetchOptions<T>
): FetchState<T> & {
  resultId: ComputedRef<string | null>
  t: (key: string) => string
} {
  const route = useRoute()
  const feedback = useFeedbackStore()
  const localeStore = useLocaleStore()

  const t = (key: string): string => getTranslation(key, localeStore.locale)

  const resultId = useRouteParam('resultId')

  const data = ref<T | null>(null)
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  const fetchData = async (): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      // Extract all route params
      const params: Record<string, string | null> = { ...route.params }

      // Build the endpoint URL
      const endpoint = options.buildEndpoint(params)

      // Fetch data
      const response = await fetchWithErrorHandling<T>(`${API_BASE_URL}${endpoint}`)

      // Apply transformation if provided
      data.value = options.transformData ? options.transformData(response) : response
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      error.value = message
      feedback.showError(`${t('loadError')}: ${message}`)
    } finally {
      isLoading.value = false
    }
  }

  return {
    data,
    isLoading,
    error,
    fetchData,
    resultId,
    t
  }
}

/**
 * Helper to extract ID from a drilldown URL
 * @param url - URL containing ID
 * @param pattern - Regex pattern to extract ID
 * @returns Extracted ID or fallback value
 */
export function extractIdFromUrl(
  url: string | undefined,
  pattern: RegExp,
  fallback: string
): string {
  if (!url) return fallback
  const match = url.match(pattern)
  return match ? match[1] : fallback
}

/**
 * Pre-built endpoint builders for common drilldown patterns
 */
export const drilldownEndpoints = {
  categoryMonths: (params: Record<string, string | null>): string =>
    `/results/${params.resultId}/accounts/${params.accountId}/categories/${params.categoryId}/months`,
  monthCategories: (params: Record<string, string | null>): string =>
    `/results/${params.resultId}/accounts/${params.accountId}/months/${params.monthId}/categories`,
  categoryMonthTransactions: (params: Record<string, string | null>): string =>
    `/results/${params.resultId}/accounts/${params.accountId}/categories/${params.categoryId}/months/${params.monthId}/transactions`
}
