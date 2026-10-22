/**
 * CSV/Excel export helpers for VueDataTable.
 *
 * Exports always produce plain text (HTML tags are stripped from
 * rendered cells), downloaded via a temporary object URL.
 * @module utils/tableExport
 */

import type { AggregateRowConfig, Column } from '../types/column'

/**
 * Export value of a cell: always plain text, no HTML
 * @param column - Column definition
 * @param value - Raw cell value
 * @param row - Row data
 * @param index - Row index
 * @returns Plain text value for the export
 */
function getExportValue(column: Column, value: unknown, row: Record<string, unknown>, index: number): string {
  // For components, use the raw value (components can't be rendered in exports)
  if (column.component) {
    if (value == null) return ''
    return String(value)
  }
  // For HTML rendering, strip tags for CSV/TSV
  if (column.renderHtml) {
    const html = column.renderHtml(value, row, index)
    return html.replace(/<[^<>]*>/g, '')
  }
  if (value == null) return ''
  return String(value)
}

/**
 * Rows of the export: filtered data rows plus the exportable
 * aggregate rows
 *
 * @param columns - Column definitions (column order)
 * @param filteredData - Filtered and sorted data rows
 * @param aggregateRows - Aggregate row configurations
 * @param aggregateRowData - Computed aggregate row data
 * @returns Export rows as arrays of cell strings
 */
export function buildExportRows(
  columns: Column[],
  filteredData: Record<string, unknown>[],
  aggregateRows: AggregateRowConfig[],
  aggregateRowData: Record<string, unknown>[]
): string[][] {
  const dataRows = filteredData.map((row, rowIndex) => {
    return columns.map(column => {
      const value = row[column.key]
      return getExportValue(column, value, row, rowIndex)
    })
  })

  const exportableAggregateRows = aggregateRows.filter(ar => ar.includeInExport !== false)
  if (exportableAggregateRows.length === 0) {
    return dataRows
  }

  const aggregateRowsForExport = aggregateRows
    .map((aggregateRow, aggregateIndex) => {
      if (aggregateRow.includeInExport === false) return null

      const rowData = aggregateRowData[aggregateIndex]
      if (!rowData) return null

      return columns.map(column => {
        const value = rowData[column.key]
        return getExportValue(column, value, rowData, aggregateIndex)
      })
    })
    .filter(Boolean) as string[][]

  dataRows.push(...aggregateRowsForExport)
  return dataRows
}

/**
 * Trigger a browser download of the given text content
 * @param content - File content
 * @param mimeType - Content MIME type
 * @param filename - Download filename
 */
function downloadTextFile(content: string, mimeType: string, filename: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

/**
 * Export data to CSV
 * @param columns - Column definitions
 * @param rows - Export rows
 * @param filename - Base filename (extension added)
 */
export function exportCsv(columns: Column[], rows: string[][], filename: string): void {
  const headers = columns.map(c => c.title).join(',')
  const csv = [headers, ...rows.map(row => row.map(v => `"${v.replaceAll('"', '""')}"`).join(','))].join('\n')
  downloadTextFile(csv, 'text/csv;charset=utf-8;', `${filename}.csv`)
}

/**
 * Export data to Excel (TSV content with an .xlsx extension, opened
 * as a spreadsheet by Excel)
 * @param columns - Column definitions
 * @param rows - Export rows
 * @param filename - Base filename (extension added)
 */
export function exportExcel(columns: Column[], rows: string[][], filename: string): void {
  const headers = columns.map(c => c.title).join('\t')
  const tsv = [headers, ...rows.map(row => row.join('\t'))].join('\n')
  downloadTextFile(tsv, 'application/vnd.ms-excel;charset=utf-8;', `${filename}.xlsx`)
}
