<script setup lang="ts">
/**
 * VueDataTable - A native Vue 3 data table component
 *
 * Replaces DataTables.net with pure Vue implementation.
 * Provides sorting, pagination, filtering, highlighting, and export.
 *
 * Features:
 * - Sortable columns
 * - Pagination
 * - Global search/filtering
 * - Row highlighting
 * - CSV/Excel export
 * - Bootstrap 5 styling
 * - Fully reactive
 *
 * SECURITY NOTE: Custom render functions use v-html, which can execute
 * arbitrary HTML/JS. This is safe because data comes from user's own CSV files.
 * If used with untrusted data, disable custom render functions.
 *
 * Usage:
 *   <VueDataTable
 *     :data="tableData"
 *     :columns="columns"
 *     id="my-table"
 *     :highlights="highlights"
 *   />
 */

import { ref, computed, onUnmounted, defineExpose, type Component } from 'vue'
import { useGettext } from 'vue3-gettext'
import { RouterLink } from 'vue-router'
import { getCssClassesForHighlights, DEFAULT_HIGHLIGHT_CONFIG } from '../../config/highlight-config'

/**
 * Column definition for VueDataTable
 */
export interface Column {
  /** Property key in data objects */
  key: string
  /** Display title */
  title: string
  /**
   * Custom HTML rendering function. Returns HTML string for v-html.
   * SECURITY: Only use with trusted content. HTML will be rendered as-is.
   */
  renderHtml?: (value: unknown, row: Record<string, unknown>, index: number) => string
  /**
   * Vue component to render in cell.
   * Enables SPA navigation, custom components, etc.
   */
  component?: Component
  /**
   * Props to pass to the component.
   * Function receives (value, row, index) and returns props object.
   */
  componentProps?: (value: unknown, row: Record<string, unknown>, index: number) => Record<string, unknown>
  /** CSS class(es) for cells. Can be string or array. */
  class?: string | string[]
  /** Enable sorting. Default: true */
  sortable?: boolean
  /** Enable searching. Default: true */
  searchable?: boolean
  /** Enable column-specific filtering. Default: true */
  filterable?: boolean
  /** CSS width (e.g., "100px", "20%") */
  width?: string
  /**
   * Route object or path for column header link.
   * When set, clicking the column header will navigate to this location.
   * Uses Vue Router's <router-link> if object, <a> tag if string.
   */
  headerTo?: string | { name: string, params?: Record<string, unknown>, query?: Record<string, unknown> }
}

/**
 * Props for VueDataTable
 */
interface Props {
  /** Table data (array of objects) */
  data: Record<string, unknown>[]
  /** Column definitions */
  columns: Column[]
  /** Table ID for DOM element */
  id?: string

  // Pagination
  /** Items per page. Default: 25 */
  pageSize?: number

  // Search
  /** Show search box. Default: true */
  showSearch?: boolean
  /** Search input placeholder. Default: "Search..." */
  searchPlaceholder?: string

  // Export
  /** Show export buttons. Default: true */
  showExport?: boolean
  /** CSV export button text. Default: "Export CSV" */
  csvText?: string
  /** Excel export button text. Default: "Export Excel" */
  excelText?: string

  // Highlighting
  /** Statistical highlights: row_id -> array of highlight class suffixes (for row-level highlighting) */
  highlights?: Record<string, string[]>
  /** Cell-level highlights: row_id -> array of highlight types (for cell-level highlighting in pivot tables) */
  cellHighlightsByRowId?: Record<string, string[]>

  // Display
  /** Show pagination controls. Default: true */
  showPagination?: boolean
  /** Show column-specific filter inputs. Default: false (opt-in) */
  showColumnFilters?: boolean
  /** Additional CSS classes for table element */
  tableClass?: string | string[]

  // Callbacks
  /** Called when a row is clicked */
  onRowClick?: (row: Record<string, unknown>, index: number) => void
}

/**
 * Public API exposed via defineExpose
 */
interface TableApi {
  /** Reset to page 1 */
  refresh: () => void
  /** Set search query */
  search: (query: string) => void
  /** Sort by column key */
  sortBy: (key: string, direction?: 'asc' | 'desc') => void
  /** Go to specific page */
  goToPage: (page: number) => void
  /** Get current page data */
  getCurrentData: () => Record<string, unknown>[]
  /** Get all filtered/sorted data */
  getFilteredData: () => Record<string, unknown>[]
  /** Set column filter value */
  setColumnFilter: (key: string, value: string) => void
  /** Clear all column filters */
  clearColumnFilters: () => void
  /** Clear specific column filter */
  clearColumnFilter: (key: string) => void
}

const props = defineProps<Props>()
const { $gettext } = useGettext()

// State
const currentPage = ref(1)
const searchQuery = ref('')
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')
const columnFilters = ref<Record<string, string>>({})

// Debounced search timeout
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Pagination
const pageSize = computed(() => props.pageSize ?? 25)
const totalItems = computed(() => filteredData.value.length)
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

/**
 * Generate smart pagination page numbers with ellipsis for large page counts.
 * Always shows: first page, last page, current page, and pages around current.
 */
const paginationPages = computed(() => {
  const pages: (number | string)[] = []
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
 * Compare two values for sorting.
 * Handles null/undefined, numbers, dates, and strings.
 */
function compareValues(a: unknown, b: unknown): number {
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
 * Get display value for a cell.
 * Handles custom render functions and formatting.
 */
function getDisplayValue(column: Column, value: unknown, row: Record<string, unknown>, index: number): string {
  if (column.renderHtml) {
    return column.renderHtml(value, row, index)
  }
  if (value == null) return ''
  return String(value)
}

/**
 * Check if column uses HTML rendering (requires v-html)
 */
function usesHtmlRendering(column: Column): boolean {
  // If component is used, it handles its own rendering
  if (column.component) return false
  // Explicit renderHtml uses HTML
  if (column.renderHtml) return true
  return false
}

/**
 * Filter and sort data based on current state.
 */
const filteredData = computed(() => {
  let result = [...props.data]

  // Apply column-specific filters
  Object.entries(columnFilters.value).forEach(([key, value]) => {
    if (value) {
      const column = props.columns.find(c => c.key === key)
      if (column && column.filterable !== false) {
        result = result.filter(row => {
          const cellValue = row[key]
          return String(cellValue).toLowerCase().includes(value.toLowerCase())
        })
      }
    }
  })

  // Apply global search filter
  const query = searchQuery.value.toLowerCase()
  if (query) {
    result = result.filter(row => {
      return props.columns.some(column => {
        if (column.searchable === false) return false
        const value = row[column.key]
        return String(value).toLowerCase().includes(query)
      })
    })
  }

  // Apply sorting
  if (sortColumn.value) {
    const column = props.columns.find(c => c.key === sortColumn.value)
    if (column) {
      result.sort((a, b) => {
        const aVal = a[column.key]
        const bVal = b[column.key]
        const comparison = compareValues(aVal, bVal)
        return comparison * (sortDirection.value === 'asc' ? 1 : -1)
      })
    }
  }

  return result
})

/**
 * Clear all column filters
 */
function clearColumnFilters(): void {
  columnFilters.value = {}
  currentPage.value = 1
}

/**
 * Clear a specific column filter
 */
function clearColumnFilter(key: string): void {
  const newFilters = { ...columnFilters.value }
  delete newFilters[key]
  columnFilters.value = newFilters
  currentPage.value = 1
}

/**
 * Set a column filter value
 */
function setColumnFilter(key: string, value: string): void {
  columnFilters.value = { ...columnFilters.value, [key]: value }
  currentPage.value = 1
}

/**
 * Get paginated data for current page.
 */
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

/**
 * Get highlight classes for a row.
 */
function getRowHighlightClasses(row: Record<string, unknown>): string[] {
  const rowId = row.row_id as string | undefined
  if (!rowId || !props.highlights) return []
  return props.highlights[rowId] ?? []
}

/**
 * Get highlight CSS classes for a specific cell.
 * Uses the cell's row_id from the _rowIds mapping.
 * @param row - The table row data
 * @param columnKey - The column key for the cell
 * @returns Array of CSS class names (without 'highlight-' prefix)
 */
function getCellHighlightClasses(row: Record<string, unknown>, columnKey: string): string[] {
  // Check if cell-level highlighting is enabled
  if (!props.cellHighlightsByRowId) return []

  // Get the _rowIds mapping from the row
  const rowIds = row._rowIds as Record<string, string> | undefined
  if (!rowIds) return []

  // Get the API row_id for this specific cell/column
  const cellRowId = rowIds[columnKey]
  if (!cellRowId) return []

  // Get the highlight types for this cell's row_id
  const highlightTypes = props.cellHighlightsByRowId[cellRowId]
  if (!highlightTypes) return []

  // Use the highlight config to resolve CSS classes
  return getCssClassesForHighlights(highlightTypes, DEFAULT_HIGHLIGHT_CONFIG)
}

/**
 * Handle column sort click.
 */
function handleSort(columnKey: string): void {
  const column = props.columns.find(c => c.key === columnKey)
  if (!column || column.sortable === false) return

  if (sortColumn.value === columnKey) {
    // Toggle direction
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    // New column
    sortColumn.value = columnKey
    sortDirection.value = 'asc'
  }
  currentPage.value = 1 // Reset to first page when sorting changes
}

/**
 * Handle search input with debounce.
 */
function handleSearch(query: string): void {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    searchQuery.value = query
    currentPage.value = 1 // Reset to first page when searching
  }, 300)
}

/**
 * Go to specific page.
 */
function goToPage(page: number): void {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

/**
 * Clear search and reset.
 */
function clearSearch(): void {
  searchQuery.value = ''
  currentPage.value = 1
}

/**
 * Get export value for a cell (always returns plain text, no HTML)
 */
function getExportValue(column: Column, value: unknown, row: Record<string, unknown>, index: number): string {
  // For components, use the raw value (components can't be rendered in exports)
  if (column.component) {
    if (value == null) return ''
    return String(value)
  }
  // For HTML rendering, get the HTML but strip tags for CSV/TSV
  if (column.renderHtml) {
    const html = column.renderHtml(value, row, index)
    // Strip HTML tags for export
    return html.replace(/<[^>]*>/g, '')
  }
  if (value == null) return ''
  return String(value)
}

/**
 * Export data to CSV.
 */
function exportCSV(): void {
  const headers = props.columns.map(c => c.title).join(',')
  const rows = filteredData.value.map((row, rowIndex) => {
    return props.columns.map(column => {
      const value = row[column.key]
      // Use export value (plain text, no HTML)
      const displayValue = getExportValue(column, value, row, rowIndex)
      // Escape for CSV (wrap in quotes, escape quotes)
      return `"${displayValue.replace(/"/g, '""')}"`
    }).join(',')
  })

  const csv = [headers, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.id || 'data'}-${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Export data to Excel (XLSX format using TSV as fallback).
 */
function exportExcel(): void {
  const headers = props.columns.map(c => c.title).join('\t')
  const rows = filteredData.value.map((row, rowIndex) => {
    return props.columns.map(column => {
      const value = row[column.key]
      const displayValue = getExportValue(column, value, row, rowIndex)
      return displayValue
    }).join('\t')
  })

  const tsv = [headers, ...rows].join('\n')
  const blob = new Blob([tsv], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.id || 'data'}-${new Date().toISOString().slice(0, 10)}.xlsx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Get table CSS classes.
 */
const tableClasses = computed(() => {
  const base = ['table', 'table-bordered', 'table-hover']
  if (props.tableClass) {
    const extra = Array.isArray(props.tableClass) ? props.tableClass : [props.tableClass]
    base.push(...extra)
  }
  return base
})

/**
 * Clean up debounce timeout on unmount.
 */
onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})

/**
 * Public API
 */
const tableApi: TableApi = {
  refresh: () => { currentPage.value = 1 },
  search: (query: string) => { searchQuery.value = query; currentPage.value = 1 },
  sortBy: (key: string, direction?: 'asc' | 'desc') => {
    sortColumn.value = key
    sortDirection.value = direction ?? 'asc'
    currentPage.value = 1
  },
  goToPage: (page: number) => goToPage(page),
  getCurrentData: () => paginatedData.value,
  getFilteredData: () => filteredData.value,
  setColumnFilter: (key: string, value: string) => setColumnFilter(key, value),
  clearColumnFilters: () => clearColumnFilters(),
  clearColumnFilter: (key: string) => clearColumnFilter(key),
}

defineExpose(tableApi)
</script>

<template>
  <div class="data-table-container">
    <!-- Search bar -->
    <div v-if="showSearch !== false" class="mb-3">
      <div class="input-group">
        <input
          type="text"
          class="form-control"
          :placeholder="searchPlaceholder ?? $gettext('Search...')"
          :value="searchQuery"
          :aria-label="$gettext('Search')"
          @input="(e) => handleSearch((e.target as HTMLInputElement).value)"
        />
        <button
          v-if="searchQuery"
          class="btn btn-outline-secondary"
          type="button"
          :aria-label="$gettext('Clear search')"
          @click="clearSearch"
        >
          &times;
        </button>
      </div>
    </div>

    <!-- Column filters clear button (shown when any column filter is active) -->
    <div v-if="props.showColumnFilters !== false && Object.keys(columnFilters).length > 0" class="mb-2">
      <button
        class="btn btn-sm btn-outline-secondary"
        type="button"
        :aria-label="$gettext('Clear all filters')"
        @click="clearColumnFilters"
      >
        {{ $gettext('Clear all filters') }}
      </button>
    </div>

    <!-- Export buttons -->
    <div v-if="showExport !== false" class="mb-3">
      <div class="btn-group">
        <button
          class="btn btn-secondary btn-sm"
          @click="exportCSV"
        >
          {{ csvText ?? $gettext('Export CSV') }}
        </button>
        <button
          class="btn btn-secondary btn-sm"
          @click="exportExcel"
        >
          {{ excelText ?? $gettext('Export Excel') }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-responsive">
      <table
        :id="id"
        :class="tableClasses"
      >
        <thead class="table-light">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="[
                'text-nowrap',
                column.class,
                {
                  'sortable': column.sortable !== false,
                  'sorted': sortColumn === column.key,
                  'sorted-asc': sortColumn === column.key && sortDirection === 'asc',
                  'sorted-desc': sortColumn === column.key && sortDirection === 'desc',
                },
              ]"
              :style="column.width ? { width: column.width } : {}"
              :aria-sort="sortColumn === column.key ? sortDirection : undefined"
              @click="column.sortable !== false ? handleSort(column.key) : undefined"
            >
              <div class="d-flex flex-column gap-1">
                <div class="d-flex align-items-center gap-2">
                  <RouterLink
                    v-if="column.headerTo && typeof column.headerTo === 'object'"
                    :to="column.headerTo"
                    class="header-link clickable"
                    @click.stop
                  >
                    {{ column.title }}
                  </RouterLink>
                  <a
                    v-else-if="column.headerTo && typeof column.headerTo === 'string'"
                    :href="column.headerTo"
                    class="header-link clickable"
                    @click.stop
                  >
                    {{ column.title }}
                  </a>
                  <span v-else>{{ column.title }}</span>
                  <template v-if="column.sortable !== false">
                    <span v-if="sortColumn === column.key" class="sort-indicator">
                      {{ sortDirection === 'asc' ? '↑' : '↓' }}
                    </span>
                    <span v-else class="sort-indicator text-muted">↕</span>
                  </template>
                </div>
                <!-- Column-specific filter input -->
                <input
                  v-if="props.showColumnFilters !== false && column.filterable !== false"
                  type="text"
                  class="form-control form-control-sm"
                  :value="columnFilters[column.key] || ''"
                  :placeholder="$gettext('Filter')"
                  :aria-label="$gettext('Filter by') + ' ' + column.title"
                  @input="(e) => setColumnFilter(column.key, (e.target as HTMLInputElement).value)"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, rowIndex) in paginatedData"
            :key="rowIndex"
            :class="{ 'table-row-clickable': onRowClick }"
            @click="onRowClick ? onRowClick(row, rowIndex) : undefined"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              :class="[
                column.class,
                ...(props.cellHighlightsByRowId ? getCellHighlightClasses(row, column.key) : getRowHighlightClasses(row).map(h => `highlight-${h}`)),
              ]"
            >
              <template v-if="column.component">
                <component
                  :is="column.component"
                  v-bind="column.componentProps ? column.componentProps(row[column.key], row, rowIndex) : {}"
                />
              </template>
              <template v-else-if="usesHtmlRendering(column)">
                <!-- SECURITY: v-html used for custom render. Only enabled with renderHtml. -->
                <!-- eslint-disable-next-line vue/no-v-html -->
                <span v-html="getDisplayValue(column, row[column.key], row, rowIndex)" />
              </template>
              <template v-else>
                {{ getDisplayValue(column, row[column.key], row, rowIndex) }}
              </template>
            </td>
          </tr>
          <tr v-if="paginatedData.length === 0">
            <td :colspan="columns.length" class="text-center text-muted py-4">
              {{ $gettext('No data found') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <nav v-if="showPagination !== false && totalPages > 1" class="mt-3">
      <ul class="pagination justify-content-center mb-0">
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <button
            class="page-link"
            :disabled="currentPage === 1"
            :aria-label="$gettext('First page')"
            @click="goToPage(1)"
          >
            {{ $gettext('First') }}
          </button>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <button
            class="page-link"
            :disabled="currentPage === 1"
            :aria-label="$gettext('Previous page')"
            @click="goToPage(currentPage - 1)"
          >
            {{ $gettext('Previous') }}
          </button>
        </li>
        <!-- Page numbers -->
        <li
          v-for="page in paginationPages"
          :key="typeof page === 'number' ? 'page-' + page : 'ellipsis'"
          class="page-item"
          :class="{ active: typeof page === 'number' && currentPage === page, disabled: typeof page !== 'number' }"
        >
          <button
            v-if="typeof page === 'number'"
            class="page-link"
            :aria-label="$gettext('Page') + ' ' + page"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <span v-else class="page-link">...</span>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <button
            class="page-link"
            :disabled="currentPage === totalPages"
            :aria-label="$gettext('Next page')"
            @click="goToPage(currentPage + 1)"
          >
            {{ $gettext('Next') }}
          </button>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <button
            class="page-link"
            :disabled="currentPage === totalPages"
            :aria-label="$gettext('Last page')"
            @click="goToPage(totalPages)"
          >
            {{ $gettext('Last') }}
          </button>
        </li>
      </ul>
      <div class="text-center text-muted small mt-2">
        {{ $gettext('Showing') }} {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalItems) }}
        {{ $gettext('of') }} {{ totalItems }} {{ $gettext('items') }}
      </div>
    </nav>
  </div>
</template>

<style scoped>
.data-table-container {
  width: 100%;
  overflow-x: auto;
}

.table-row-clickable {
  cursor: pointer;
}

.table-row-clickable:hover td {
  background-color: rgba(0, 0, 0, 0.05);
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.sorted {
  background-color: rgba(0, 0, 0, 0.1);
}

.sort-indicator {
  font-size: 0.8rem;
}

th {
  vertical-align: middle;
}

.header-link {
  color: inherit;
  text-decoration: none;
}

.header-link:hover {
  color: inherit;
  text-decoration: underline;
}

/* Highlight classes - these are added dynamically based on highlights prop */
:global(.highlight-positive) {
  background-color: rgba(40, 167, 69, 0.15);
}
:global(.highlight-negative) {
  background-color: rgba(220, 53, 69, 0.15);
}
:global(.highlight-warning) {
  background-color: rgba(255, 193, 7, 0.15);
}
:global(.highlight-info) {
  background-color: rgba(23, 162, 184, 0.15);
}
</style>
