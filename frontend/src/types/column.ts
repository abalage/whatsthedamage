/**
 * Table column and aggregate configuration types shared by
 * VueDataTable and its consumers (pages, composables).
 * @module types/column
 */

import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

/**
 * Aggregate configuration for individual columns
 */
interface ColumnAggregateConfig {
/** Type override for this column (defaults to global config) */
type?: 'average' | 'sum' | 'min' | 'max' | 'count' | 'custom' | 'none'
/** Custom calculation for this column only */
customCalculator?: (data: Record<string, unknown>[]) => unknown
/** Custom formatter for this column's summary */
formatter?: (value: unknown) => string
/** Whether to show summary for this column (default: true) */
enabled?: boolean
/** Custom label for this column's summary cell */
label?: string
}


/**
 * Column definition for VueDataTable
 */
export interface Column {
/** Property key in data objects */
key: string
/** Display title */
title: string
/**
   * Plain-text value formatter.
   * Returns the display text for the cell; the output is rendered
   * escaped (never interpreted as HTML).
   */
formatValue?: (value: unknown, row?: Record<string, unknown>, index?: number) => string
/**
   * Vue component to render in cell.
   * Enables SPA navigation, custom components, etc.
   */
component?: Component
/**
   * Props to pass to the component.
   * Function receives (value, row, index) and returns props object.
   * row and index are optional for backwards compatibility.
   */
componentProps?: (value: unknown, row?: Record<string, unknown>, index?: number) => Record<string, unknown>
/** CSS class(es) for cells. Can be string or array. */
class?: string | string[]
/** Enable sorting. Default: true */
sortable?: boolean
/** Enable searching. Default: true */
searchable?: boolean
/** Enable column-specific filtering. Default: true */
filterable?: boolean
/**
   * Fixed-choice filter: renders a <select> instead of a text input.
   * Filtering is an exact match on the option value (language-agnostic:
   * values are stable ids, labels may be translated).
   */
filterOptions?: Array<{ value: string; label: string }>
/** CSS width (e.g., "100px", "20%") */
width?: string
/**
   * Route object or path for column header link.
   * When set, clicking the column header will navigate to this location.
   * Uses Vue Router's <router-link> if object, <a> tag if string.
   */
headerTo?: RouteLocationRaw
/** Aggregate configuration for this column */
aggregate?: ColumnAggregateConfig
}


/**
 * Aggregate row configuration for VueDataTable
 */
export interface AggregateRowConfig {
/** Unique identifier for this summary row */
id?: string
/** Display label for the row (default: depends on type) */
label?: string
/** Type of summary calculation */
type: 'average' | 'sum' | 'min' | 'max' | 'count' | 'custom'
/** Position: 'header', 'footer', or 'both' (default: 'footer') */
position?: 'header' | 'footer' | 'both'
/** Which columns to include (default: all columns) */
columns?: string[] | ((columnKey: string) => boolean)
/** Explicitly exclude columns */
excludeColumns?: string[]
/** CSS classes for this row */
class?: string | string[]
/** Custom calculation function (when type is 'custom') */
customCalculator?: (data: Record<string, unknown>[], columnKey: string) => unknown
/** Custom formatter for the summary value (optional) */
formatter?: (value: unknown, columnKey: string) => string
/** Priority/order for multiple summary rows (default: 0) */
priority?: number
}
