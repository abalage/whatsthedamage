/**
 * Cell-level highlight resolution for VueDataTable.
 *
 * Maps a cell's highlight types (keyed by API row id) to CSS classes
 * using the shared highlight configuration.
 * @module composables/useTableHighlight
 */

import { getCssClassesForHighlights, DEFAULT_HIGHLIGHT_CONFIG } from '../config/highlight-config'

/** Return type of useTableHighlight */
interface UseTableHighlightReturn {
  /**
   * Get highlight CSS classes for a specific cell. Uses the cell's
   * row_id from the row's `_rowIds` mapping.
   * @param row - The table row data
   * @param columnKey - The column key for the cell
   * @returns Array of CSS class names (without 'highlight-' prefix)
   */
  getCellHighlightClasses: (row: Record<string, unknown>, columnKey: string) => string[]
}

/**
 * Cell highlight resolution for a data table.
 *
 * @param cellHighlightsByRowId - Getter for the highlight map:
 *     row_id -> array of highlight types
 * @returns Cell highlight class resolver
 */
export function useTableHighlight(
  cellHighlightsByRowId: () => Record<string, string[]> | undefined
): UseTableHighlightReturn {
  function getCellHighlightClasses(row: Record<string, unknown>, columnKey: string): string[] {
    // Check if cell-level highlighting is enabled
    const highlights = cellHighlightsByRowId()
    if (!highlights) return []

    // Get the _rowIds mapping from the row
    const rowIds = row._rowIds as Record<string, string> | undefined
    if (!rowIds) return []

    // Get the API row_id for this specific cell/column
    const cellRowId = rowIds[columnKey]
    if (!cellRowId) return []

    // Get the highlight types for this cell's row_id
    const highlightTypes = highlights[cellRowId]
    if (!highlightTypes) return []

    // Use the highlight config to resolve CSS classes
    return getCssClassesForHighlights(highlightTypes, DEFAULT_HIGHLIGHT_CONFIG)
  }

  return { getCellHighlightClasses }
}
