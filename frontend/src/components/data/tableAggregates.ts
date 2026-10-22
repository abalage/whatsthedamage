/**
 * Pure aggregate-row logic for VueDataTable: built-in calculators,
 * column inclusion rules, and effective-config resolution.
 *
 * Extracted from the component so it is unit-testable without a DOM.
 * @module components/data/tableAggregates
 */

import type { AggregateRowConfig, Column } from '../../types/column'

/**
 * Type of a computed aggregate cell value
 */
export type AggregateValue = number | string | null

/**
 * Built-in aggregate calculators keyed by aggregate type
 */
export const AGGREGATE_CALCULATORS: Record<string, (data: Record<string, unknown>[], columnKey: string) => AggregateValue> = {
  average: (data, columnKey) => {
    const values = data.map(row => row[columnKey]).filter(v => v !== null && v !== undefined)
    if (values.length === 0) return null
    const numericValues = values.map(Number).filter(v => !Number.isNaN(v))
    return numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length
  },
  sum: (data, columnKey) => {
    const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
    return numericValues.length > 0 ? numericValues.reduce((sum, val) => sum + val, 0) : null
  },
  min: (data, columnKey) => {
    const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
    return numericValues.length > 0 ? Math.min(...numericValues) : null
  },
  max: (data, columnKey) => {
    const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
    return numericValues.length > 0 ? Math.max(...numericValues) : null
  },
  count: (data, columnKey) => {
    return data.filter(row => row[columnKey] !== null && row[columnKey] !== undefined).length
  }
}

/**
 * Marker property identifying aggregate rows within the table
 */
export const AGGREGATE_ROW_MARKER = '_isAggregateRow'

/**
 * Check if a row is an aggregate row (for template use)
 * @param row - Table row
 * @returns Whether the row is an aggregate row
 */
export function isAggregateRow(row: Record<string, unknown>): boolean {
  return row[AGGREGATE_ROW_MARKER] === true
}

/**
 * Check if a column should be included in an aggregate row
 * @param aggregateRow - Aggregate row configuration
 * @param columnKey - Column key to check
 * @returns Whether the column participates in the aggregate
 */
export function shouldIncludeColumn(aggregateRow: AggregateRowConfig, columnKey: string): boolean {
  // If columns are explicitly specified, only include those
  if (aggregateRow.columns) {
    if (typeof aggregateRow.columns === 'function') {
      return aggregateRow.columns(columnKey)
    }
    return aggregateRow.columns.includes(columnKey)
  }

  // If columns are explicitly excluded, exclude those
  if (aggregateRow.excludeColumns?.includes(columnKey)) {
    return false
  }

  return true
}

/**
 * Effective aggregate config for a column: column-level overrides
 * the global aggregate row configuration
 * @param aggregateRow - Global aggregate row configuration
 * @param column - Column definition
 * @returns Effective configuration
 */
export function getEffectiveAggregateConfig(aggregateRow: AggregateRowConfig, column: Column): {
  type: string
  customCalculator?: (data: Record<string, unknown>[]) => unknown
  formatter?: (value: unknown) => string
  enabled?: boolean
  label?: string
} {
  const columnAggregate = column.aggregate

  if (columnAggregate?.enabled === false) {
    return { type: 'none' }
  }

  return {
    type: columnAggregate?.type ?? aggregateRow.type,
    customCalculator: columnAggregate?.customCalculator,
    formatter: columnAggregate?.formatter,
    enabled: columnAggregate?.enabled,
    label: columnAggregate?.label
  }
}

/**
 * Default label for an aggregate type
 * @param type - Aggregate type
 * @param gettext - Translation function
 * @returns Translated label
 */
export function getDefaultLabelForType(type: string, gettext: (key: string) => string): string {
  const labels: Record<string, string> = {
    average: gettext('Average'),
    sum: gettext('Sum'),
    min: gettext('Min'),
    max: gettext('Max'),
    count: gettext('Count'),
    custom: gettext('Aggregate')
  }
  return labels[type] || gettext('Aggregate')
}
