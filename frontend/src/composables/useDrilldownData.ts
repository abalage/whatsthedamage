/**
 * Composable for handling drilldown page data fetching and state management
 * Simplified version that uses focused composables internally
 * @module composables/useDrilldownData
 */

import { computed, nextTick, type ComputedRef, type Ref } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useRouteParams, type StringRouteParams } from './useRouteParams.js'
import { useApiData } from './useApiData.js'
import { usePageTitle, type TitleFormat } from './usePageTitle.js'
import type { BreadcrumbItem } from './useBreadcrumbs.js'

/**
 * Page configuration for drilldown pages
 */
export interface DrilldownPageConfig<T> {
  /**
   * Custom fetch function that takes route params and returns data
   * This is the only supported pattern (buildEndpoint has been removed)
   */
  fetchData: (params: StringRouteParams) => Promise<T>
  /**
   * Optional data transformation function
   */
  transformData?: (data: unknown) => T
  /**
   * Base translation key for auto-generating page title
   * Used with titleFormat and titleExtractor to create titles like "Transactions: Food - Jan 2025"
   */
  titleBaseKey?: string
  /**
   * Format pattern for auto-generating page title
   * - 'category':        "{titleBaseKey}: {categoryName}"
   * - 'month':          "{titleBaseKey}: {formattedMonth}"
   * - 'category-month': "{titleBaseKey}: {categoryName} - {formattedMonth}"
   * - 'custom':         Use titleBaseKey only (no auto-formatting)
   */
  titleFormat?: TitleFormat
  /**
   * Extract categoryId and/or monthTimestamp from API response data for title generation
   * Only needed when using titleFormat (not 'custom')
   */
  titleExtractor?: (data: T) => { categoryId?: string; monthTimestamp?: number }
  /**
   * Breadcrumb items - can be static or function that takes data and returns items
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
  errorMessageKey?: string
}

/**
 * Result of useDrilldownData composable
 */
export interface DrilldownResult<T> {
  data: Ref<T | null>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  fetchData: () => Promise<void>
  resultId: ComputedRef<string | null>
  accountId: ComputedRef<string | null>
  categoryId: ComputedRef<string | null>
  monthId: ComputedRef<string | null>
  t: (key: string) => string
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
 * - DataTables initialization callbacks
 *
 * Note: The deprecated buildEndpoint pattern has been removed. Use fetchData only.
 *
 * @param config - Page configuration
 * @returns Drilldown result with data, state, and computed properties
 *
 * @example
 * ```typescript
 * // Basic usage with built-in title generation
 * const { data, isLoading, error, fetchData, pageTitle, breadcrumbItems } =
 *   useDrilldownData<CategoryMonthsResponse>({
 *     fetchData: async (params) => fetchCategoryMonths(params),
 *     titleBaseKey: 'Category Details',
 *     titleFormat: 'category',
 *     titleExtractor: (data) => ({ categoryId: data.category_id }),
 *     breadcrumbItems: () => [
 *       { name: 'Home', to: '/' },
 *       { name: 'Categories', to: { name: 'results', query: { resultId } } },
 *       { name: 'Category Details', active: true }
 *     ]
 *   })
 *
 * onMounted(fetchData)
 * ```
 */
export function useDrilldownData<T>(
  config: DrilldownPageConfig<T>
): DrilldownResult<T> {
  const route = useRoute()
  const { $gettext } = useGettext()

  const t = (key: string): string => $gettext(key)

  // Route params using the new composable
  const { resultId, accountId, categoryId, monthId, convertParamsToString } = useRouteParams()

  // Create params computed for API calls
  const stringParams = computed(() => convertParamsToString(route.params))

  // Use the focused useApiData composable
  const createFetchFn = (): (() => Promise<T>) => {
    return async () => {
      if (!resultId.value) {
        throw new Error(t('missingRequiredParameters'))
      }
      const response = await config.fetchData(stringParams.value)
      return config.transformData ? config.transformData(response) : response
    }
  }

  const { data, isLoading, error, fetchData: baseFetchData } = useApiData<T>({
    fetchFn: createFetchFn(),
    t,
    errorMessageKey: config.errorMessageKey
  })

  // Wrap fetchData with onDataLoaded callback
  const fetchData = async (): Promise<void> => {
    await baseFetchData()
    if (data.value && config.onDataLoaded) {
      await nextTick()
      await config.onDataLoaded(data.value)
    }
  }

  // Page title generation
  const titleOptions = computed(() => {
    let extractedCategoryId: string | undefined
    let extractedMonthTimestamp: number | undefined

    if (config.titleExtractor && data.value) {
      const extracted = config.titleExtractor(data.value)
      extractedCategoryId = extracted.categoryId
      extractedMonthTimestamp = extracted.monthTimestamp
    }

    return {
      baseKey: config.titleBaseKey ?? 'Details',
      format: config.titleFormat ?? 'custom' as TitleFormat,
      categoryId: extractedCategoryId ?? categoryId.value,
      monthTimestamp: extractedMonthTimestamp ?? (monthId.value ? Number(monthId.value) : undefined),
      t
    }
  })

  const { pageTitle } = usePageTitle(titleOptions)

  // Breadcrumbs generation - compute directly from data for reactivity
  const breadcrumbItems = computed<BreadcrumbItem[]>(() => {
    if (typeof config.breadcrumbItems === 'function') {
      return config.breadcrumbItems(data.value)
    }
    return config.breadcrumbItems ?? []
  })

  // Expose the route params as computed refs for backward compatibility
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
    breadcrumbItems
  }
}


