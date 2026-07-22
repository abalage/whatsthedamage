/**
 * Composable for handling drilldown page data fetching and state management
 * @module composables/useDrilldownData
 */

import { ref, computed, nextTick, type ComputedRef, type Ref } from 'vue'
import { useRoute, type RouteLocationRaw } from 'vue-router'
import { useFeedbackStore } from '../stores/feedback.js'
import { useCategoriesStore } from '../stores/categories.js'
import { useGettext } from 'vue3-gettext'
import { fetchWithErrorHandling, API_BASE_URL } from '../js/api.js'
import { formatMonthYear } from '../js/dateUtils.js'
import type { TranslationKeys } from '../vue-shim.js'

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
 * Route parameters type that may contain string arrays from route.params
 */
type RouteParams = Record<string, string | string[] | null>

/**
 * String-only route parameters type
 */
type StringRouteParams = Record<string, string | null>

/**
 * Page configuration for drilldown pages
 */
export interface DrilldownPageConfig<T> {
  /**
   * Function to build the API endpoint URL from route parameters
   * (deprecated: use fetchData instead for type-safe API calls)
   * Note: params may contain string arrays from route.params
   */
  buildEndpoint?: (params: RouteParams) => string
  /**
   * Custom fetch function that takes route params and returns data
   * Use this for type-safe API calls instead of buildEndpoint
   */
  fetchData?: (params: StringRouteParams) => Promise<T>
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
   * Use titleBaseKey/titleFormat/titleExtractor for built-in patterns instead
   * @param data - The API response data
   * @returns The formatted page title string
   */
  getPageTitle?: (data: T) => string
  /**
   * Static page title if getPageTitle is not provided
   * Fallback chain: getPageTitle -> pageTitle -> auto-generated -> 'Details'
   */
  pageTitle?: string
  /**
   * Base translation key for auto-generating page title
   * Used with titleFormat and titleExtractor to create titles like "Transactions: Food - Jan 2025"
   * @example 'Transactions'
   */
  titleBaseKey?: string
  /**
   * Format pattern for auto-generating page title
   * - 'category':        "{titleBaseKey}: {categoryName}"
   * - 'month':          "{titleBaseKey}: {formattedMonth}"
   * - 'category-month': "{titleBaseKey}: {categoryName} - {formattedMonth}"
   * - 'custom':         Use getPageTitle function (default behavior)
   */
  titleFormat?: 'category' | 'month' | 'category-month' | 'custom'
  /**
   * Extract categoryId and/or monthTimestamp from API response data for title generation
   * Only needed when using titleFormat (not 'custom')
   * @param data - The API response data
   * @returns Object with categoryId and/or monthTimestamp used for title formatting
   * @example
   * ```typescript
   * titleExtractor: (data) => ({
   *   categoryId: data.category_id,
   *   monthTimestamp: data.month_timestamp
   * })
   * ```
   */
  titleExtractor?: (data: T) => { categoryId?: string; monthTimestamp?: number }
  /**
   * Breadcrumb items - can be static or function that takes data
   */
  breadcrumbItems?: BreadcrumbItem[] | ((data: T | null) => BreadcrumbItem[])
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
 * // Using built-in title generation (recommended)
 * const { data, isLoading, error, fetchData, pageTitle, breadcrumbItems } =
 *   useDrilldownData<CategoryMonthsResponse>({
 *     fetchData: async (params) => fetchCategoryMonths(params),
 *     titleBaseKey: 'Category Details',
 *     titleFormat: 'category',
 *     titleExtractor: (data) => ({ categoryId: data.category_id }),
 *     breadcrumbItems: [
 *       { name: 'Home', to: '/' },
 *       { name: 'Categories', to: { name: 'results', query: { resultId } } },
 *       { name: 'Category Details', active: true }
 *     ]
 *   })
 *
 * // Using custom getPageTitle function (for complex cases)
 * const { data, isLoading, error, fetchData, pageTitle, breadcrumbItems } =
 *   useDrilldownData<CategoryMonthsResponse>({
 *     buildEndpoint: drilldownEndpoints.categoryMonths,
 *     tableId: 'datatable-category',
 *     getPageTitle: (d) => `Details for Category: ${useCategoriesStore().getCategoryDisplayName(d.category_id)}`,
 *     breadcrumbItems: (d) => [
 *       { name: 'Home', to: '/' },
 *       { name: 'Results', to: { name: 'results', query: { resultId: d?.result_id } } },
 *       { name: 'Category Details' }
 *     ],
 *     onDataLoaded: (data) => {
 *       globalThis.exportCsvText = t('Export CSV')
 *       globalThis.highlights = data.highlights || {}
 *       globalThis.initMainPage()
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
  const { $gettext } = useGettext()

  const t = (key: string): string => $gettext(key)

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
    // Custom function takes precedence
    if (data.value && config.getPageTitle) {
      return config.getPageTitle(data.value)
    }
    // Static title
    if (config.pageTitle) {
      return config.pageTitle
    }
    // Auto-generate from config
    if (data.value && config.titleBaseKey && config.titleExtractor) {
      const base = t(config.titleBaseKey)
      const extracted = config.titleExtractor(data.value)
      const { categoryId, monthTimestamp } = extracted

      switch (config.titleFormat) {
        case 'category': {
          if (categoryId) {
            const categoriesStore = useCategoriesStore()
            const displayName = categoriesStore.getCategoryDisplayName(categoryId)
            return displayName ? `${base}: ${displayName}` : base
          }
          return base
        }
        case 'month': {
          if (monthTimestamp !== undefined) {
            return `${base}: ${formatMonthYear(monthTimestamp)}`
          }
          return base
        }
        case 'category-month': {
          const displayName = categoryId ? useCategoriesStore().getCategoryDisplayName(categoryId) : ''
          const formattedMonth = monthTimestamp !== undefined ? formatMonthYear(monthTimestamp) : ''
          if (displayName && formattedMonth) {
            return `${base}: ${displayName} - ${formattedMonth}`
          }
          if (displayName) return `${base}: ${displayName}`
          if (formattedMonth) return `${base}: ${formattedMonth}`
          return base
        }
        case 'custom':
        default:
          break
      }
    }
    return t('Details')
  })

  // Computed breadcrumb items
  const breadcrumbItems = computed(() => {
    if (typeof config.breadcrumbItems === 'function') {
      return config.breadcrumbItems(data.value)
    }
    return config.breadcrumbItems ?? []
  })

  const convertParamsToString = (
    params: RouteParams
  ): StringRouteParams => {
    const stringParams: StringRouteParams = {}
    for (const [key, value] of Object.entries(params)) {
      if (value === null) {
        stringParams[key] = null
      } else if (Array.isArray(value)) {
        stringParams[key] = value.length > 0 ? value[0] : null // eslint-disable-line no-magic-numbers
      } else if (typeof value === 'string') {
        stringParams[key] = value
      } else {
        stringParams[key] = null
      }
    }
    return stringParams
  }

  const fetchWithConfig = async (
    params: RouteParams
  ): Promise<T> => {
    if (config.fetchData) {
      const stringParams = convertParamsToString(params)
      return config.fetchData(stringParams)
    }
    if (config.buildEndpoint) {
      const endpoint = config.buildEndpoint(params)
      const rawResponse = await fetchWithErrorHandling<T>(`${API_BASE_URL}${endpoint}`)
      return rawResponse
    }
    throw new Error('Either fetchData or buildEndpoint must be provided in config')
  }

  const processResponse = (response: T): void => {
    data.value = config.transformData ? config.transformData(response) : response
    error.value = null
    isLoading.value = false
  }

  const handleError = (err: unknown): void => {
    const message = err instanceof Error ? err.message : String(err)
    error.value = message
    const errorKey = config.errorMessageKey ?? 'loadError'
    feedback.showError(`${t(errorKey)}: ${message}`)
    isLoading.value = false
  }

  const fetchData = async (): Promise<void> => {
    if (!resultId.value) {
      error.value = t('missingRequiredParameters')
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const params: RouteParams = { ...route.params }
      const response = await fetchWithConfig(params)
      processResponse(response)
      await nextTick()
      if (config.onDataLoaded && data.value) {
        await config.onDataLoaded(data.value)
      }
    } catch (err) {
      handleError(err)
    }
  }

  return {
    data: data as Ref<T | null>,
    isLoading,
    error,
    fetchData,
    resultId,
    accountId,
    categoryId,
    monthId,
    t,
    pageTitle,
    breadcrumbItems
  }
}

/**
 * Helper to extract ID from a drilldown URL
 * @param url - URL containing ID
 * @param pattern - Regex pattern to extract ID
 * @returns Extracted ID or fallback value
 */
function extractIdFromUrl(
  url: string | undefined,
  pattern: RegExp,
  fallback: string
): string {
  if (!url) return fallback
  const match = pattern.exec(url)
  return match ? match[1] : fallback
}
