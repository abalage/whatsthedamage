<!--
  TableCell - Single cell renderer for VueDataTable.

  Renders the column's Vue component, its custom HTML (v-html), or the
  plain string value. Used for body rows and header/footer aggregate
  rows, removing the triplicated rendering logic from the table.
-->

<script setup lang="ts">
import type { Column } from '../../types/column'

withDefaults(defineProps<{
  /** Column definition of the cell */
  column: Column
  /** Raw cell value */
  value: unknown
  /** Row data of the cell */
  row: Record<string, unknown>
  /** Row index (passed to render functions) */
  index: number
  /**
   * Skip the component rendering and show plain text instead
   * (used for aggregate rows, which display values as text)
   */
  asText?: boolean
}>(), {
  asText: false
})

/**
 * Whether the column renders custom HTML (requires v-html)
 */
function usesHtmlRendering(column: Column): boolean {
  if (column.component) return false
  return Boolean(column.renderHtml)
}

/**
 * Display value of the cell: custom render function result or the
 * stringified raw value
 */
function getDisplayValue(column: Column, value: unknown, row: Record<string, unknown>, index: number): string {
  if (column.renderHtml) {
    return column.renderHtml(value, row, index)
  }
  if (value == null) return ''
  return String(value)
}
</script>

<template>
  <component
    :is="column.component"
    v-if="column.component && !asText"
    v-bind="column.componentProps ? column.componentProps(value, row, index) : {}"
  />
  <!-- SECURITY: v-html used for custom render. Only enabled with renderHtml. -->
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else-if="usesHtmlRendering(column)" v-html="getDisplayValue(column, value, row, index)" />
  <template v-else>
    {{ getDisplayValue(column, value, row, index) }}
  </template>
</template>
