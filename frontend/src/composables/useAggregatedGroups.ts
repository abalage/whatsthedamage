/**
 * Shared helpers for the aggregated drilldown pages
 * (MonthCategoriesList, CategoryMonthsList): both display the groups
 * of an AggregatedTransactionsResponse as a VueDataTable with a total
 * footer and cell highlighting.
 * @module composables/useAggregatedGroups
 */

import { computed, watch, type ComputedRef, type Ref } from 'vue'
import { useStatisticalStore } from '../stores/statistical'
import type { AggregateRowConfig } from '../types/column'
import type { AggregatedTransactionsResponse, TransactionListItem } from '../types/api'

/**
 * Sum of the amounts of a group of transactions
 * @param txns - Transactions of one group
 * @returns Sum of the amounts, treating missing amounts as zero
 */
export function calculateTotalForTransactions(txns: TransactionListItem[]): number {
  return txns.reduce((sum, txn) => sum + (txn.amount || 0), 0)
}

/**
 * Options for buildGroupRows
 */
export interface GroupRowOptions {
  /** Column key holding the group label ('category_id' or 'month') */
  keyColumn: string
  /** Formats the group key into its display label */
  labelFormatter: (key: string) => string
  /** Row id used for cell highlighting (defaults to the group key) */
  rowIdOf?: (key: string) => string
  /** Extra fields added to each row (e.g. navigation context) */
  extraFields?: (key: string) => Record<string, unknown>
}

/**
 * Build VueDataTable rows from the groups of an AggregatedTransactionsResponse
 *
 * Each row carries the group total, its formatted display value, and the
 * _rowIds mapping that links the total column to its highlight row id.
 *
 * @param groups - Grouped transactions keyed by group id
 * @param options - Row construction options
 * @returns Table rows, one per group
 */
export function buildGroupRows(
  groups: Record<string, TransactionListItem[]>,
  options: GroupRowOptions
): Array<Record<string, unknown>> {
  return Object.entries(groups).map(([groupKey, txns]) => {
    const total = calculateTotalForTransactions(txns)
    const rowId = options.rowIdOf ? options.rowIdOf(groupKey) : groupKey
    return {
      [options.keyColumn]: options.labelFormatter(groupKey),
      total,
      total_display: total.toFixed(2),
      row_id: rowId,
      ...(options.extraFields ? options.extraFields(groupKey) : {}),
      // Map total column to its row_id for cell-level highlighting
      _rowIds: {
        total: rowId
      }
    }
  })
}

/**
 * Total-sum aggregate row for the groups table footer
 * @param gettext - Translation function of the page
 * @param keyColumn - Column key receiving the "Total" label
 * @returns Aggregate row configuration
 */
export function sumAggregateRowConfig(
  gettext: (key: string) => string,
  keyColumn: string
): AggregateRowConfig {
  return {
    id: 'total-sum',
    type: 'custom',
    position: 'footer',
    includeInExport: true,
    class: 'fw-bold bg-surface-primary text-on-primary',
    customCalculator: (data: Record<string, unknown>[], columnKey: string): string | number => {
      if (columnKey === keyColumn) return gettext('Total')
      if (columnKey === 'total') {
        const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
        return numericValues.reduce((sum, val) => sum + val, 0)
      }
      return ''
    }
  }
}

/**
 * Average aggregate row for the groups table footer
 * @param gettext - Translation function of the page
 * @param keyColumn - Column key receiving the "Average" label
 * @returns Aggregate row configuration
 */
export function averageAggregateRowConfig(
  gettext: (key: string) => string,
  keyColumn: string
): AggregateRowConfig {
  return {
    id: 'total-average',
    type: 'custom',
    position: 'footer',
    includeInExport: true,
    class: 'fw-bold bg-surface-secondary text-on-dark',
    customCalculator: (data: Record<string, unknown>[], columnKey: string): string | number | null => {
      if (columnKey === keyColumn) return gettext('Average')
      if (columnKey === 'total') {
        const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
        return numericValues.length > 0
          ? numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length
          : null
      }
      return ''
    }
  }
}

/**
 * Syncs the highlights of a fetched aggregation response into the
 * statistical store and exposes the cell highlight map for the table
 *
 * @param data - Fetched aggregation response
 * @returns Cell highlight map keyed by row id
 */
export function useStatisticalHighlights(
  data: Ref<AggregatedTransactionsResponse | null>
): { cellHighlightsByRowId: ComputedRef<Record<string, string[]>> } {
  const statisticalStore = useStatisticalStore()

  // Initialize highlights from API when data loads
  watch(() => data.value, (newData) => {
    if (newData?.highlights) {
      statisticalStore.setHighlights(newData.highlights)
    }
  }, { immediate: true })

  const cellHighlightsByRowId = computed(() => {
    return statisticalStore.highlights || {}
  })

  return { cellHighlightsByRowId }
}
