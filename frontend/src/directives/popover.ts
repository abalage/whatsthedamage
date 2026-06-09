/**
 * Vue Directive for Bootstrap Popover
 * 
 * This directive provides Vue-idiomatic lifecycle management for Bootstrap popovers.
 * It automatically initializes popovers when elements are mounted, updates them
 * when content changes, and destroys them when elements are unmounted.
 * 
 * Usage:
 *   <span v-popover="{ content: 'My popover content', placement: 'top' }">
 *     Hover me
 *   </span>
 * 
 * Options:
 *   - content: Popover content (required)
 *   - placement: 'top', 'right', 'bottom', 'left' (default: 'top')
 *   - html: Allow HTML in content (default: true)
 *   - sanitize: Sanitize HTML content (default: true)
 *   - trigger: How popover is triggered ('click', 'hover', 'focus', 'manual') (default: 'hover focus')
 *   - customClass: Additional CSS class for popover
 */

import type { Directive, DirectiveBinding } from 'vue'

/**
 * Popover directive options
 */
export interface PopoverOptions {
  /** Popover content */
  content: string
  /** Popover placement */
  placement?: 'top' | 'right' | 'bottom' | 'left'
  /** Allow HTML in content */
  html?: boolean
  /** Sanitize HTML content */
  sanitize?: boolean
  /** Trigger method */
  trigger?: string
  /** Custom CSS class */
  customClass?: string
}

/**
 * Initialize a Bootstrap popover on an element
 */
function initPopover(el: HTMLElement, options: PopoverOptions): void {
  const bootstrap = (globalThis as unknown as Window).bootstrap as { Popover?: unknown } | undefined
  
  if (!bootstrap?.Popover) {
    // eslint-disable-next-line no-console
    console.warn('[popover directive] Bootstrap Popover not available')
    return
  }
  
  // Destroy existing popover first
  const existing = (bootstrap.Popover as { getInstance: (el: Element) => unknown }).getInstance(el)
  if (existing && typeof existing === 'object' && 'dispose' in existing) {
    (existing as { dispose: () => void }).dispose()
  }
  
  // Initialize new popover
  new (bootstrap.Popover as new (el: Element, opts: unknown) => unknown)(el, {
    content: options.content,
    placement: options.placement ?? 'top',
    html: options.html !== false,
    sanitize: options.sanitize !== false,
    trigger: options.trigger ?? 'hover focus',
    customClass: options.customClass
  })
}

/**
 * Destroy Bootstrap popover on an element
 */
function destroyPopover(el: HTMLElement): void {
  const bootstrap = (globalThis as unknown as Window).bootstrap as { Popover?: { getInstance: (el: Element) => unknown } } | undefined
  
  if (bootstrap?.Popover) {
    const instance = bootstrap.Popover.getInstance(el)
    if (instance && typeof instance === 'object' && 'dispose' in instance) {
      (instance as { dispose: () => void }).dispose()
    }
  }
}

/**
 * Vue directive for Bootstrap popover
 */
export const popoverDirective: Directive<HTMLElement, PopoverOptions> = {
  mounted(el: HTMLElement, binding: DirectiveBinding<PopoverOptions>) {
    if (binding.value?.content) {
      initPopover(el, binding.value)
    }
  },
  
  updated(el: HTMLElement, binding: DirectiveBinding<PopoverOptions>) {
    // Only re-initialize if content changed
    if (binding.oldValue?.content !== binding.value?.content) {
      if (binding.value?.content) {
        initPopover(el, binding.value)
      } else {
        destroyPopover(el)
      }
    }
  },
  
  unmounted(el: HTMLElement) {
    destroyPopover(el)
  }
}
