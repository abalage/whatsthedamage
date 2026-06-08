<script setup lang="ts">
/**
 * TableLinkWithPopover - A link component with Bootstrap popover support.
 * 
 * Combines TableLink functionality with Bootstrap popover for displaying
 * additional information on hover/focus. Designed for use in VueDataTable cells.
 * 
 * Usage:
 *   In VueDataTable column definition:
 *   {
 *     key: 'myColumn',
 *     title: 'My Column',
 *     component: TableLinkWithPopover,
 *     componentProps: (value, row, index) => ({
 *       to: `/path/${row.id}`,
 *       class: 'clickable',
 *       children: value,
 *       popoverContent: row.details,
 *       popoverPlacement: 'top',
 *       popoverCustomClass: 'popover-wide'
 *     })
 *   }
 */

import { computed } from 'vue'
import { RouterLink } from 'vue-router'

interface Props {
  /**
   * Target URL or route object.
   * - String: Used as href for <a> tag
   * - Route object: Used with <router-link> for SPA navigation
   */
  to: string | { name: string, params?: Record<string, unknown>, query?: Record<string, unknown> }
  /** CSS class(es) for the link */
  class?: string | string[]
  /** Link content (text) */
  children?: string
  /** Popover content (HTML or text) */
  popoverContent?: string
  /** Popover placement: 'top', 'right', 'bottom', 'left' */
  popoverPlacement?: string
  /** Custom CSS class for popover */
  popoverCustomClass?: string
}

const props = defineProps<Props>()

/**
 * Get the CSS classes as a string
 */
const linkClass = computed(() => {
  if (!props.class) return undefined
  return Array.isArray(props.class) ? props.class.join(' ') : props.class
})

/**
 * Get popover options for v-popover directive
 */
const popoverOptions = computed(() => {
  if (!props.popoverContent) return undefined
  return {
    content: props.popoverContent,
    placement: props.popoverPlacement || 'top',
    html: true,
    sanitize: true,
    customClass: props.popoverCustomClass,
    trigger: 'hover focus'
  }
})
</script>

<template>
  <span v-if="popoverOptions" v-popover="popoverOptions">
    <RouterLink
      v-if="typeof to === 'object'"
      :to="to"
      :class="linkClass"
      tabindex="0"
    >
      <slot>{{ children }}</slot>
    </RouterLink>
    <a
      v-else
      :href="to"
      :class="linkClass"
      tabindex="0"
    >
      <slot>{{ children }}</slot>
    </a>
  </span>
  <span v-else>
    <RouterLink
      v-if="typeof to === 'object'"
      :to="to"
      :class="linkClass"
      tabindex="0"
    >
      <slot>{{ children }}</slot>
    </RouterLink>
    <a
      v-else
      :href="to"
      :class="linkClass"
      tabindex="0"
    >
      <slot>{{ children }}</slot>
    </a>
  </span>
</template>
