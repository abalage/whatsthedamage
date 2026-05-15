/**
 * Composable for handling drilldown page data fetching and state management
 * @module composables/useDrilldownData
 */

import { ref, computed, nextTick, type ComputedRef, type Ref } from 'vue'
import { useRoute, type RouteLocationRaw } from 'vue-router'
import { useFeedbackStore } from '../stores/feedback'
import { useLocaleStore } from '../stores/locale'
import { getTranslation, type TranslationKeys } from '../stores/translations'
import { fetchWithErrorHandling, API_BASE_URL } from '../js/api'

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
 * Breadcrumb item configuration
 */
export interface BreadcrumbItem {
  name: string
  to?: RouteLocationRaw
  active?: boolean
}

/**
 * Navigation button configuration
 */
export interface NavButton {
  text: string
  to: RouteLocationRaw
  variant?: string
  size?: 'sm' | 'lg'
}

/**
 * Page configuration for drilldown pages
 */
export interface DrilldownPageConfig<T> {
  /**
   * Function to build the API endpoint URL from route parameters
   */
  buildEndpoint: (params: Record<string, string | null>) => string
  /**
   * Optional data transformation function
   */
  transformData?: (data: unknown) => T
  /**
   * Table ID for DataTables initialization (optional)
   */
  tableId?: string
  /**
   * Function to generate page title from data
   */
  getPageTitle?: (data: T) => string
  /**
   * Static page title if getPageTitle is not provided
   */
  pageTitle?: string
  /**
   * Breadcrumb items - can be static or function that takes data
   */
  breadcrumbItems?: BreadcrumbItem[] | ((data: T | null) => BreadcrumbItem[])
  /**
   * Navigation buttons to display
   */
  navButtons?: NavButton[]
  /**
   * Custom initialization hook called after data is loaded
   * Use this for DataTables initialization or other page-specific setup
   */
  onDataLoaded?: (data: T) => void | Promise<void>
  /**
   * Error message key for i18n
   */
  errorMessageKey?: TranslationKeys
}

/**
 * Common data fetching state
 */
interface FetchState<T> {
  data: Ref<T | null>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  fetchData: () => Promise<void>
}

/**
 * Result of useDrilldownData composable
 */
export interface DrilldownResult<T> extends FetchState<T> {
  resultId: ComputedRef<string | null>
  accountId: ComputedRef<string | null>
  categoryId: ComputedRef<string | null>
  monthId: ComputedRef<string | null>
  t: (key: TranslationKeys) => string
  pageTitle: ComputedRef<string>
  breadcrumbItems: ComputedRef<BreadcrumbItem[]>
  navButtons: NavButton[]
}

/**
 * Creates a drilldown data fetcher with common patterns for drilldown pages
 *
 * This composable handles:
 * - Route parameter extraction with type safety
 * - API data fetching with error handling
 * - Loading and error states
 * - Page titles and breadcrumbs
 * - Navigation buttons
 * - DataTables initialization callbacks
 *
 * @param config - Page configuration
 * @returns Drilldown result with data, state, and computed properties
 *
 * @example
 * ```typescript
 * const { data, isLoading, error, fetchData, pageTitle, breadcrumbItems } =
 *   useDrilldownData<CategoryMonthsResponse>({
 *     buildEndpoint: drilldownEndpoints.categoryMonths,
 *     tableId: 'datatable-category',
 *     getPageTitle: (d) => `Details for Category: ${d.category_name}`,
 *     breadcrumbItems: (d) => [
 *       { name: 'Home', to: '/' },
 *       { name: 'Results', to: { name: 'results', query: { resultId: d?.result_id } } },
 *       { name: 'Category Details' }
 *     ],
 *     navButtons: [
 *       { text: 'Back to Results', to: { name: 'results', query: { resultId } }, variant: 'secondary' }
 *     ],
 *     onDataLoaded: (data) => {
 *       window.exportCsvText = t('Export CSV')
 *       window.highlights = data.highlights || {}
 *       window.initMainPage()
 *     }
 *   })
 *
 * onMounted(fetchData)
 * ```
 */
export function useDrilldownData<T>(
  config: DrilldownPageConfig<T>
): DrilldownResult<T> {
  const route = useRoute()
  const feedback = useFeedbackStore()
  const localeStore = useLocaleStore()

  const t = (key: TranslationKeys): string => getTranslation(key, localeStore.locale as 'en' | 'hu')

  // Extract route parameters with type safety
  const resultId = useRouteParam('resultId')
  const accountId = useRouteParam('accountId')
  const categoryId = useRouteParam('categoryId')
  const monthId = useRouteParam('monthId')

  // State
  const data = ref<T | null>(null)
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  // Computed page title
  const pageTitle = computed(() => {
    if (data.value && config.getPageTitle) {
      return config.getPageTitle(data.value)
    }
    return config.pageTitle ?? t('Details')
  })

  // Computed breadcrumb items
  const breadcrumbItems = computed(() => {
    if (typeof config.breadcrumbItems === 'function') {
      return config.breadcrumbItems(data.value)
    }
    return config.breadcrumbItems ?? []
  })

  const fetchData = async (): Promise<void> => {
    // Check for required parameters based on the endpoint
    if (!resultId.value) {
      error.value = t('missingRequiredParameters')
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null

    try {
      // Extract all route params
      const params: Record<string, string | null> = { ...route.params }

      // Build the endpoint URL
      const endpoint = config.buildEndpoint(params)

      // Fetch data
      const response = await fetchWithErrorHandling<T>(`${API_BASE_URL}${endpoint}`)

      // Apply transformation if provided
      data.value = config.transformData ? config.transformData(response) : response
      error.value = null

      // Set isLoading to false BEFORE calling onDataLoaded so the template renders
      isLoading.value = false

      // Wait for Vue to render the tables with the new data
      await nextTick()

      // Call custom initialization hook if provided
      if (config.onDataLoaded && data.value) {
        await config.onDataLoaded(data.value)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      error.value = message
      const errorKey = config.errorMessageKey ?? 'loadError'
      feedback.showError(`${t(errorKey)}: ${message}`)
      isLoading.value = false
    }
  }

  return {
    data,
    isLoading,
    error,
    fetchData,
    resultId,
    accountId,
    categoryId,
    monthId,
    t,
    pageTitle,
    breadcrumbItems,
    navButtons: config.navButtons ?? []
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
  return match ? match[1] : fallback // eslint-disable-line no-magic-numbers
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
