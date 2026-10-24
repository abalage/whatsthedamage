/**
 * Filtering state for VueDataTable: per-column filters plus the
 * debounced global search query.
 * @module composables/useTableFiltering
 */

import { onUnmounted, ref, type Ref } from 'vue'
import type { Column } from '../types/column'

/** Debounce delay of the global search input, in milliseconds */
const SEARCH_DEBOUNCE_MS = 300

/** Options for useTableFiltering */
interface UseTableFilteringOptions {
  /** Called after a filter or the search query changed (the table resets its page) */
  onFiltersChanged?: () => void
}

/** Return type of useTableFiltering */
interface UseTableFilteringReturn {
  /** Current global search query */
  searchQuery: Ref<string>
  /** Current per-column filter values, keyed by column key */
  columnFilters: Ref<Record<string, string>>
  /** Handle search input with debounce */
  handleSearch: (query: string) => void
  /** Clear the search query */
  clearSearch: () => void
  /** Set the search query directly (public table API) */
  search: (query: string) => void
  /** Set a column filter value */
  setColumnFilter: (key: string, value: string) => void
  /** Clear a specific column filter */
  clearColumnFilter: (key: string) => void
  /** Clear all column filters */
  clearColumnFilters: () => void
  /** Filter a data array by the current state (pure, returns a new array) */
  filterData: (data: Record<string, unknown>[]) => Record<string, unknown>[]
}

/**
 * Filter state and helpers for a data table.
 *
 * @param columns - Getter for the current column definitions
 * @param options - Callbacks invoked when the filter state changes
 * @returns Filter state and operations
 */
export function useTableFiltering(
  columns: () => Column[],
  options: UseTableFilteringOptions = {}
): UseTableFilteringReturn {
  const searchQuery = ref('')
  const columnFilters = ref<Record<string, string>>({})

  // Debounced search timeout
  let searchTimeout: ReturnType<typeof setTimeout> | null = null

  /**
   * Handle search input with debounce.
   * @param query - Raw search input value
   */
  function handleSearch(query: string): void {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchTimeout = setTimeout(() => {
      searchQuery.value = query
      options.onFiltersChanged?.()
    }, SEARCH_DEBOUNCE_MS)
  }

  /**
   * Clear search and reset.
   */
  function clearSearch(): void {
    searchQuery.value = ''
    options.onFiltersChanged?.()
  }

  /**
   * Set the search query directly.
   * @param query - Search query
   */
  function search(query: string): void {
    searchQuery.value = query
    options.onFiltersChanged?.()
  }

  /**
   * Clear all column filters.
   */
  function clearColumnFilters(): void {
    columnFilters.value = {}
    options.onFiltersChanged?.()
  }

  /**
   * Clear a specific column filter.
   * @param key - Column key of the filter to clear
   */
  function clearColumnFilter(key: string): void {
    const newFilters = { ...columnFilters.value }
    delete newFilters[key]
    columnFilters.value = newFilters
    options.onFiltersChanged?.()
  }

  /**
   * Set a column filter value.
   * @param key - Column key to filter
   * @param value - Filter value
   */
  function setColumnFilter(key: string, value: string): void {
    columnFilters.value = { ...columnFilters.value, [key]: value }
    options.onFiltersChanged?.()
  }

  /**
   * Filter a data array by the current column filters and search query.
   * @param data - Data rows to filter
   * @returns Filtered copy of the data
   */
  function filterData(data: Record<string, unknown>[]): Record<string, unknown>[] {
    let result = [...data]

    // Apply column-specific filters
    Object.entries(columnFilters.value).forEach(([key, value]) => {
      if (value) {
        const column = columns().find(c => c.key === key)
        if (column && column.filterable !== false) {
          // Fixed-choice filters match the raw value exactly; text filters
          // fall back to case-insensitive substring matching
          const matches = column.filterOptions
            ? (row: Record<string, unknown>): boolean => String(row[key]) === value
            : (row: Record<string, unknown>): boolean => String(row[key]).toLowerCase().includes(value.toLowerCase())
          result = result.filter(matches)
        }
      }
    })

    // Apply global search filter
    const query = searchQuery.value.toLowerCase()
    if (query) {
      result = result.filter(row => {
        return columns().some(column => {
          if (column.searchable === false) return false
          const value = row[column.key]
          return String(value).toLowerCase().includes(query)
        })
      })
    }

    return result
  }

  // Clean up debounce timeout on unmount
  onUnmounted(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
  })

  return {
    searchQuery,
    columnFilters,
    handleSearch,
    clearSearch,
    search,
    setColumnFilter,
    clearColumnFilter,
    clearColumnFilters,
    filterData
  }
}
