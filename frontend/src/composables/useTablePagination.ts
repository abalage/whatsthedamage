/**
 * Pagination state for VueDataTable: current page, page count, and
 * the smart page-number list with ellipsis.
 * @module composables/useTablePagination
 */

import { computed, ref, type ComputedRef, type Ref } from 'vue'

/** Return type of useTablePagination */
interface UseTablePaginationReturn {
  /** Current page number (1-based) */
  currentPage: Ref<number>
  /** Configured items per page */
  pageSize: ComputedRef<number>
  /** Total item count of the filtered data */
  totalItems: ComputedRef<number>
  /** Total page count */
  totalPages: ComputedRef<number>
  /** Page numbers with ellipsis placeholders for the pagination controls */
  paginationPages: ComputedRef<Array<number | string>>
  /** Go to a specific page, clamped to the valid range */
  goToPage: (page: number) => void
  /** Reset to the first page */
  reset: () => void
}

/**
 * Pagination state and helpers for a data table.
 *
 * @param totalItems - Getter for the total item count (the table
 *     passes the length of its filtered data)
 * @param pageSize - Getter for the configured items per page
 * @returns Pagination state and operations
 */
export function useTablePagination(
  totalItems: () => number,
  pageSize: () => number
): UseTablePaginationReturn {
  const currentPage = ref(1)
  const itemsPerPage = computed(pageSize)
  const itemCount = computed(totalItems)
  const totalPages = computed(() => Math.ceil(itemCount.value / itemsPerPage.value))

  /**
   * Generate smart pagination page numbers with ellipsis for large
   * page counts. Always shows: first page, last page, current page,
   * and pages around current.
   */
  const paginationPages = computed((): Array<number | string> => {
    const pages: Array<number | string> = []
    const maxVisible = 7
    const half = Math.floor(maxVisible / 2)

    if (totalPages.value <= maxVisible) {
      // Show all pages if not too many
      for (let i = 1; i <= totalPages.value; i++) {
        pages.push(i)
      }
    } else {
      // Always show first page
      pages.push(1)

      // Show pages around current page
      let start = Math.max(2, currentPage.value - half)
      let end = Math.min(totalPages.value - 1, currentPage.value + half)

      // Adjust if we're at the edges
      if (currentPage.value <= half + 1) {
        end = maxVisible - 1
      } else if (currentPage.value >= totalPages.value - half) {
        start = totalPages.value - maxVisible + 2
      }

      // Add ellipsis if needed before middle pages
      if (start > 2) {
        pages.push('...')
      }

      // Add middle pages
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      // Add ellipsis if needed after middle pages
      if (end < totalPages.value - 1) {
        pages.push('...')
      }

      // Always show last page
      pages.push(totalPages.value)
    }

    return pages
  })

  /**
   * Go to a specific page.
   * @param page - Page number (ignored when out of range)
   */
  function goToPage(page: number): void {
    if (page < 1 || page > totalPages.value) return
    currentPage.value = page
  }

  /**
   * Reset to the first page.
   */
  function reset(): void {
    currentPage.value = 1
  }

  return {
    currentPage,
    pageSize: itemsPerPage,
    totalItems: itemCount,
    totalPages,
    paginationPages,
    goToPage,
    reset
  }
}
