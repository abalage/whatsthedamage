<script setup lang="ts">
/**
 * VueDataTable - A native Vue 3 data table component
 *
 * Replaces DataTables.net with pure Vue implementation.
 * Provides sorting, pagination, filtering, and highlighting.
 *
 * Features:
 * - Sortable columns
 * - Pagination
 * - Global search/filtering
 * - Row highlighting
 * - Bootstrap 5 styling
 * - Fully reactive
 *
 * Usage:
 *   <VueDataTable
 *     :data="tableData"
 *     :columns="columns"
 *     id="my-table"
 *   />
 *
 * NOTE: For sorting to work correctly, cell values should be primitive types
 * (numbers, strings, dates) or null/undefined. Object values will be converted
 * to strings using String(value) for comparison, which may not produce expected
 * results (e.g., { amount: 100 } becomes "[object Object]").
 */

import { computed, type CSSProperties } from 'vue'
import { useGettext } from 'vue3-gettext'
import { RouterLink } from 'vue-router'
import type { Column, AggregateRowConfig } from '../../types/column'
import { useTableSorting } from '../../composables/useTableSorting'
import { useTableFiltering } from '../../composables/useTableFiltering'
import { useTablePagination } from '../../composables/useTablePagination'
import { useTableHighlight } from '../../composables/useTableHighlight'
import {
  AGGREGATE_CALCULATORS,
  AGGREGATE_ROW_MARKER,
  getDefaultLabelForType,
  getEffectiveAggregateConfig,
  isAggregateRow,
  shouldIncludeColumn
} from './tableAggregates'
import TableCell from './TableCell.vue'

export type { Column, AggregateRowConfig }




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

  // Highlighting
  /** Cell-level highlights: row_id -> array of highlight types (for cell-level highlighting in pivot tables) */
  cellHighlightsByRowId?: Record<string, string[]>

  // Aggregate rows
  /** Aggregate row configurations (replaces footerData) */
  aggregateRows?: AggregateRowConfig[]
  /** CSS classes for aggregate rows in header */
  aggregateHeaderRowClass?: string | string[]
  /** CSS classes for aggregate rows in footer */
  aggregateFooterRowClass?: string | string[]

  // Display
  /** Show pagination controls. Default: true */
  showPagination?: boolean
  /** Show column-specific filter inputs. Default: false (opt-in) */
  showColumnFilters?: boolean
  /** Additional CSS classes for table element */
  tableClass?: string | string[]
  /** Additional CSS classes for the wrapper container */
  wrapperClass?: string | string[]
  /** Inline styles for the wrapper container */
  wrapperStyle?: CSSProperties

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

// Emitted when the "Clear all filters" button resets all column filters,
// so pages can also reset their own toolbar filters
const emit = defineEmits(['cleared-filters'])
const { $gettext } = useGettext()

// Computed aggregate row data
const aggregateRowData = computed(() => {
  if (!props.aggregateRows?.length || !props.columns?.length) return []

  return props.aggregateRows.map(aggregateRow => {
    const row: Record<string, unknown> = {}
    // Mark this as an aggregate row
    row[AGGREGATE_ROW_MARKER] = true

    props.columns.forEach(column => {
      // Check if column should be included in this aggregate row
      const columnIncluded = shouldIncludeColumn(aggregateRow, column.key)
      if (!columnIncluded) {
        row[column.key] = ''
        return
      }

      // Get the effective aggregate config (column-level overrides global)
      const effectiveConfig = getEffectiveAggregateConfig(aggregateRow, column)

      // Skip if aggregate is disabled for this column
      if (effectiveConfig.type === 'none' || effectiveConfig.enabled === false) {
        row[column.key] = ''
        return
      }

      // Calculate the aggregate value
      const dataForCalculation = filteredData.value
      let value: unknown

      if (effectiveConfig.type === 'custom' && column.aggregate?.customCalculator) {
        // Column-level custom calculator
        value = column.aggregate.customCalculator(dataForCalculation)
      } else if (aggregateRow.type === 'custom' && aggregateRow.customCalculator) {
        // Global custom calculator
        value = aggregateRow.customCalculator(dataForCalculation, column.key)
      } else {
        // Built-in calculator
        const calculator = AGGREGATE_CALCULATORS[effectiveConfig.type || aggregateRow.type]
        value = calculator ? calculator(dataForCalculation, column.key) : null
      }

      // Apply formatter
      const effectiveFormatter = column.aggregate?.formatter || aggregateRow.formatter
      row[column.key] = effectiveFormatter ? effectiveFormatter(value, column.key) : value
    })

    // Set row label for the first column (or as specified)
    if (props.columns.length > 0) {
      const firstColumnKey = props.columns[0].key
      const label = aggregateRow.label || getDefaultLabelForType(aggregateRow.type, $gettext)
      // Only set label if not already set by custom calculator
      if (row[firstColumnKey] === '' || row[firstColumnKey] == null) {
        row[firstColumnKey] = label
      }
    }

    return row
  })
})

/**
 * Whether a cell needs the TableCell component (custom component or
 * formatted value). Plain cells render inline for performance: mounting
 * a component instance per plain cell measurably slows large tables.
 * Body-row component cells are also rendered inline; TableCell remains
 * for formatted cells and the aggregate rows.
 */
function needsCellComponent(column: Column): boolean {
  return Boolean(column.component || column.formatValue)
}

// Separate aggregate rows for header and footer
const headerAggregateData = computed(() => {
  return aggregateRowData.value.filter((_, index) => {
    const aggregateRow = props.aggregateRows?.[index]
    const position = aggregateRow?.position ?? 'footer'
    return position === 'header' || position === 'both'
  })
})

const footerAggregateData = computed(() => {
  return aggregateRowData.value.filter((_, index) => {
    const aggregateRow = props.aggregateRows?.[index]
    const position = aggregateRow?.position ?? 'footer'
    return position === 'footer' || position === 'both'
  })
})

// State and behavior live in dedicated composables; this component is
// the orchestration (props wiring, aggregate rows, template)
const { sortColumn, sortDirection, ariaSortValue, handleSort, sortBy, sortData } = useTableSorting(
  () => props.columns,
  { onSortChange: () => pagination.reset() }
)

const {
  searchQuery,
  columnFilters,
  handleSearch,
  clearSearch,
  search,
  setColumnFilter,
  clearColumnFilter,
  clearColumnFilters,
  filterData
} = useTableFiltering(
  () => props.columns,
  { onFiltersChanged: () => pagination.reset() }
)

/**
 * Filter and sort data based on current state.
 */
const filteredData = computed(() => sortData(filterData(props.data)))

const pagination = useTablePagination(
  () => filteredData.value.length,
  () => props.pageSize ?? 25
)
const { currentPage, pageSize: itemsPerPage, totalItems, totalPages, paginationPages, goToPage } = pagination

const { getCellHighlightClasses } = useTableHighlight(() => props.cellHighlightsByRowId)

/**
 * Get paginated data for current page.
 */
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredData.value.slice(start, end)
})

/**
 * Clear all column filters and notify the page so it can reset its
 * own toolbar filters as well.
 */
function clearAllColumnFilters(): void {
  clearColumnFilters()
  emit('cleared-filters')
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
 * Public API
 */
const tableApi: TableApi = {
  refresh: () => pagination.reset(),
  search,
  sortBy,
  goToPage: (page: number) => goToPage(page),
  getCurrentData: () => paginatedData.value,
  getFilteredData: () => filteredData.value,
  setColumnFilter: (key: string, value: string) => setColumnFilter(key, value),
  clearColumnFilters: () => clearAllColumnFilters(),
  clearColumnFilter: (key: string) => clearColumnFilter(key),
}

defineExpose(tableApi)
</script>

<template>
  <div class="data-table-container" :class="wrapperClass" :style="wrapperStyle">
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
          class="btn bg-surface-base text-secondary border-secondary hover-bg-surface-secondary px-2 py-1 text-sm rounded-sm"
          type="button"
          :aria-label="$gettext('Clear search')"
          @click="clearSearch"
        >
          &times;
        </button>
      </div>
    </div>

    <!-- Column filters toolbar: always-visible clear button plus
         page-provided filter toggle buttons -->
    <div v-if="props.showColumnFilters !== false" class="mb-2 d-flex flex-wrap gap-2 align-items-center">
      <button
        class="btn bg-surface-base text-secondary border-secondary hover-bg-surface-secondary px-2 py-1 text-sm rounded-sm"
        type="button"
        :aria-label="$gettext('Clear all filters')"
        @click="clearAllColumnFilters"
      >
        {{ $gettext('Clear all filters') }}
      </button>
      <slot name="filter-actions"></slot>
    </div>

    <!-- Table -->
    <div class="table-responsive">
      <table
        :id="id"
        :class="tableClasses"
      >
        <thead class="bg-surface-primary text-on-primary">
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
              :aria-sort="sortColumn === column.key ? ariaSortValue : undefined"
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
                    <span v-else class="sort-indicator text-secondary">↕</span>
                  </template>
                </div>
                <!-- Column-specific filter control -->
                <select
                  v-if="props.showColumnFilters !== false && column.filterable !== false && column.filterOptions"
                  class="form-select form-select-sm"
                  :value="columnFilters[column.key] || ''"
                  :aria-label="$gettext('Filter by') + ' ' + column.title"
                  @change="(e) => setColumnFilter(column.key, (e.target as HTMLSelectElement).value)"
                >
                  <option value="">{{ $gettext('All') }}</option>
                  <option
                    v-for="option in column.filterOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
                <input
                  v-else-if="props.showColumnFilters !== false && column.filterable !== false"
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
          <!-- Aggregate header rows -->
          <tr
            v-for="(aggregateRow, aggregateIndex) in headerAggregateData"
            :key="`aggregate-header-${props.aggregateRows?.[aggregateIndex]?.id || aggregateIndex}`"
            :class="[aggregateHeaderRowClass, props.aggregateRows?.[aggregateIndex]?.class]"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              :class="[
                column.class,
                ...getCellHighlightClasses(aggregateRow, column.key),
              ]"
            >
              <TableCell
                v-if="needsCellComponent(column)"
                :column="column"
                :value="aggregateRow[column.key]"
                :row="aggregateRow"
                :index="aggregateIndex"
                :as-text="isAggregateRow(aggregateRow)"
              />
              <template v-else>{{ aggregateRow[column.key] ?? '' }}</template>
            </td>
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
                ...getCellHighlightClasses(row, column.key),
              ]"
            >
              <!-- Extension point: a #cell-<key> slot wins over every
                   built-in rendering. Use it for new custom cells
                   instead of growing the column API. -->
              <slot
                v-if="$slots[`cell-${column.key}`]"
                :name="`cell-${column.key}`"
                :value="row[column.key]"
                :row="row"
                :index="rowIndex"
              />
              <component
                :is="column.component"
                v-else-if="column.component"
                v-bind="column.componentProps ? column.componentProps(row[column.key], row, rowIndex) : {}"
              />
              <TableCell
                v-else-if="needsCellComponent(column)"
                :column="column"
                :value="row[column.key]"
                :row="row"
                :index="rowIndex"
              />
              <template v-else>{{ row[column.key] ?? '' }}</template>
            </td>
          </tr>
          <tr v-if="paginatedData.length === 0">
            <td :colspan="columns.length" class="text-center text-secondary py-4">
              {{ $gettext('No data available') }}
            </td>
          </tr>
        </tbody>
        <!-- Aggregate footer rows -->
        <tfoot v-if="footerAggregateData.length > 0" :class="aggregateFooterRowClass">
          <tr
            v-for="(aggregateRow, aggregateIndex) in footerAggregateData"
            :key="`aggregate-footer-${props.aggregateRows?.[aggregateIndex]?.id || aggregateIndex}`"
            :class="[aggregateFooterRowClass, props.aggregateRows?.[aggregateIndex]?.class]"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              :class="[
                column.class,
                ...getCellHighlightClasses(aggregateRow, column.key),
              ]"
            >
              <TableCell
                v-if="needsCellComponent(column)"
                :column="column"
                :value="aggregateRow[column.key]"
                :row="aggregateRow"
                :index="aggregateIndex"
                :as-text="isAggregateRow(aggregateRow)"
              />
              <template v-else>{{ aggregateRow[column.key] ?? '' }}</template>
            </td>
          </tr>
        </tfoot>
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
      <div class="text-center text-secondary small mt-2">
        {{ $gettext('Showing') }} {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, totalItems) }}
        {{ $gettext('of') }} {{ totalItems }} {{ $gettext('items') }}
      </div>
    </nav>
  </div>
</template>

<style scoped>
.data-table-container {
  width: auto;
  max-width: 100%;
  min-width: 0;
  overflow-x: auto;
}

.table-row-clickable {
  cursor: pointer;
}

.table-row-clickable:hover td {
  background-color: var(--color-text-on-light-05);
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background-color: var(--color-text-on-light-05);
}

.sorted {
  background-color: var(--color-text-on-light-10);
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
</style>
