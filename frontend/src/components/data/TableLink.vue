<script setup lang="ts">
/**
 * TableLink - A Vue Router-aware link component for use in VueDataTable cells.
 * 
 * This component enables SPA navigation within table cells, preventing full page reloads.
 * It automatically uses Vue Router's <router-link> when a route object is provided,
 * and falls back to a standard <a> tag for external links.
 * 
 * Usage:
 *   In VueDataTable column definition:
 *   {
 *     key: 'myColumn',
 *     title: 'My Column',
 *     component: TableLink,
 *     componentProps: (value, row, index) => ({
 *       to: `/path/${row.id}`,
 *       class: 'clickable',
 *       children: value
 *     })
 *   }
 * 
 * Or with route object:
 *   componentProps: (value, row, index) => ({
 *     to: { name: 'route-name', params: { id: row.id } },
 *     children: value
 *   })
 */

import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

interface Props {
  /**
   * Target URL or route object.
   * - String: Used as href for <a> tag
   * - Route object: Used with <router-link> for SPA navigation
   */
  to: RouteLocationRaw
  /** CSS class(es) for the link */
  class?: string | string[]
  /** Link content (text) */
  children?: string
}

const props = defineProps<Props>()

/**
 * Get the CSS classes as a string
 */
const linkClass = computed(() => {
  if (!props.class) return undefined
  return Array.isArray(props.class) ? props.class.join(' ') : props.class
})
</script>

<template>
  <RouterLink
    v-if="typeof to === 'object'"
    :to="to"
    :class="linkClass"
  >
    <slot>{{ children }}</slot>
  </RouterLink>
  <a
    v-else
    :href="to"
    :class="linkClass"
  >
    <slot>{{ children }}</slot>
  </a>
</template>
