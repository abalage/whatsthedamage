/**
 * Sorting state and comparator for VueDataTable.
 *
 * Owns the sort column/direction state, the ARIA sort attribute, and
 * the value comparator; applying the sort to a data array is a pure
 * function so the table can compose it after filtering.
 * @module composables/useTableSorting
 */

import { computed, ref, type ComputedRef, type Ref } from 'vue'
import type { Column } from '../types/column'

/** Options for useTableSorting */
interface UseTableSortingOptions {
  /** Called after the sort state changed (the table resets its page) */
  onSortChange?: () => void
}

/** Return type of useTableSorting */
interface UseTableSortingReturn {
  /** Currently sorted column key, or null when unsorted */
  sortColumn: Ref<string | null>
  /** Current sort direction */
  sortDirection: Ref<'asc' | 'desc'>
  /** ARIA sort attribute value for the sorted column */
  ariaSortValue: ComputedRef<'ascending' | 'descending' | undefined>
  /** Handle a sort click on a column header */
  handleSort: (columnKey: string) => void
  /** Set the sort state directly (public table API) */
  sortBy: (key: string, direction?: 'asc' | 'desc') => void
  /** Sort a data array by the current state (pure, returns a copy) */
  sortData: (data: Record<string, unknown>[]) => Record<string, unknown>[]
}

/**
 * Compare two values for sorting.
 * Handles null/undefined, numbers, dates, and strings.
 * @param a - First value
 * @param b - Second value
 * @returns Negative when a sorts before b, positive when after, 0 on equal
 */
export function compareValues(a: unknown, b: unknown): number {
  // Handle null/undefined
  if (a == null && b == null) return 0
  if (a == null) return -1
  if (b == null) return 1

  // Numbers
  if (typeof a === 'number' && typeof b === 'number') {
    return a - b
  }

  // Dates (check both for Date instances)
  if (a instanceof Date && b instanceof Date) {
    return a.getTime() - b.getTime()
  }
  if (a instanceof Date) return -1
  if (b instanceof Date) return 1

  // Strings (fallback)
  return String(a).localeCompare(String(b))
}

/**
 * Sort state and helpers for a data table.
 *
 * @param columns - Getter for the current column definitions
 * @param options - Callbacks invoked when the sort state changes
 * @returns Sort state and operations
 */
export function useTableSorting(
  columns: () => Column[],
  options: UseTableSortingOptions = {}
): UseTableSortingReturn {
  const sortColumn = ref<string | null>(null)
  const sortDirection = ref<'asc' | 'desc'>('asc')

  // ARIA sort attribute value (maps 'asc'/'desc' to
  // 'ascending'/'descending' for accessibility)
  const ariaSortValue = computed(() => {
    if (!sortColumn.value) return undefined
    return sortDirection.value === 'asc' ? 'ascending' : 'descending'
  })

  /**
   * Handle column sort click.
   * @param columnKey - Key of the clicked column
   */
  function handleSort(columnKey: string): void {
    const column = columns().find(c => c.key === columnKey)
    if (!column || column.sortable === false) return

    if (sortColumn.value === columnKey) {
      // Toggle direction
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      // New column
      sortColumn.value = columnKey
      sortDirection.value = 'asc'
    }
    options.onSortChange?.()
  }

  /**
   * Set the sort state directly.
   * @param key - Column key to sort by
   * @param direction - Sort direction (default: ascending)
   */
  function sortBy(key: string, direction?: 'asc' | 'desc'): void {
    sortColumn.value = key
    sortDirection.value = direction ?? 'asc'
    options.onSortChange?.()
  }

  /**
   * Sort a data array by the current sort state.
   * @param data - Data rows to sort
   * @returns Sorted copy of the data
   */
  function sortData(data: Record<string, unknown>[]): Record<string, unknown>[] {
    if (!sortColumn.value) return data
    const column = columns().find(c => c.key === sortColumn.value)
    if (!column) return data

    return [...data].sort((a, b) => {
      const comparison = compareValues(a[column.key], b[column.key])
      return comparison * (sortDirection.value === 'asc' ? 1 : -1)
    })
  }

  return { sortColumn, sortDirection, ariaSortValue, handleSort, sortBy, sortData }
}
