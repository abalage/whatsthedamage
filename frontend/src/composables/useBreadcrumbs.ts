/**
 * Breadcrumb type definitions
 * @module composables/useBreadcrumbs
 */

import type { RouteLocationRaw } from 'vue-router'

/**
 * Breadcrumb item configuration
 */
export interface BreadcrumbItem {
  name: string
  to?: RouteLocationRaw
  active?: boolean
}
