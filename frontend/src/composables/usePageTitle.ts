/**
 * Composable for generating page titles with i18n support
 * @module composables/usePageTitle
 */

import { computed, type ComputedRef } from 'vue'
import { useCategoriesStore } from '../stores/categories.js'
import { formatMonthYear } from '../js/dateUtils.js'

/**
 * Title format patterns
 */
export type TitleFormat = 'category' | 'month' | 'category-month' | 'custom'

/**
 * Options for page title generation
 */
export interface PageTitleOptions {
  /**
   * Base translation key for the page title
   */
  baseKey: string
  /**
   * Format pattern for auto-generating the title
   */
  format: TitleFormat
  /**
   * Category ID for title generation (used with 'category' and 'category-month' formats)
   */
  categoryId?: string | null
  /**
   * Month timestamp for title generation (used with 'month' and 'category-month' formats)
   */
  monthTimestamp?: number | null
  /**
   * i18n translation function
   */
  t: (key: string) => string
}

/**
 * Result of usePageTitle composable
 */
export interface PageTitleResult {
  pageTitle: ComputedRef<string>
}

/**
 * Type guard to check if value is a ComputedRef
 */
function isComputedRef<T>(value: unknown): value is ComputedRef<T> {
  return typeof value === 'object' && value !== null && 'value' in value
}

/**
 * Generates page titles with support for i18n and dynamic data
 * @param options - Configuration options (plain object or computed ref)
 * @returns Object with computed page title
 */
export function usePageTitle(
  options: PageTitleOptions | ComputedRef<PageTitleOptions>
): PageTitleResult {
  const categoriesStore = useCategoriesStore()

  const resolvedOptions = computed(() =>
    isComputedRef<PageTitleOptions>(options) ? options.value : options
  )

  const pageTitle = computed(() => {
    const opts = resolvedOptions.value
    const base = opts.t(opts.baseKey)
    const { categoryId, monthTimestamp } = opts

    switch (opts.format) {
      case 'category':
        if (categoryId) {
          const displayName = categoriesStore.getCategoryDisplayName(categoryId)
          return displayName ? `${base}: ${displayName}` : base
        }
        return base

      case 'month':
        if (monthTimestamp !== undefined && monthTimestamp !== null) {
          return `${base}: ${formatMonthYear(monthTimestamp)}`
        }
        return base

      case 'category-month': {
        const displayName = categoryId ? categoriesStore.getCategoryDisplayName(categoryId) : ''
        const formattedMonth = monthTimestamp !== undefined && monthTimestamp !== null ? formatMonthYear(monthTimestamp) : ''
        if (displayName && formattedMonth) {
          return `${base}: ${displayName} - ${formattedMonth}`
        }
        if (displayName) return `${base}: ${displayName}`
        if (formattedMonth) return `${base}: ${formattedMonth}`
        return base
      }

      case 'custom':
      default:
        return base
    }
  })

  return { pageTitle }
}
