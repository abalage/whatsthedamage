/**
 * Main JavaScript utilities for What's the Damage v2
 * Now using VueDataTable instead of DataTables.net
 */

import * as bootstrapNs from 'bootstrap';

/**
 * Type for Bootstrap Popover from globalThis.bootstrap
 */
interface BootstrapPopoverStatic {
    getInstance(element: Element): unknown;
    new (element: Element, options?: unknown): unknown;
}

/**
 * Type for globalThis.bootstrap
 */
interface WindowBootstrap {
    Popover?: BootstrapPopoverStatic;
    [key: string]: unknown;
}

/**
 * Global storage for popover instances - allows bulk operations if needed
 */
let popoverInstances: unknown[] = [];

/**
 * Initialize Bootstrap popovers
 */
export function initMainPage(): void {
    // Use globalThis.bootstrap which is set by src/main.ts
    const bootstrap = (globalThis as unknown as Window).bootstrap as WindowBootstrap | undefined;
    if (bootstrap?.Popover) {
        const Popover = bootstrap.Popover;
        const popoverTriggerList = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverInstances = [];
        popoverTriggerList.forEach((popoverTriggerEl: Element) => {
            // Destroy existing popover if it exists
            const existingPopover = Popover.getInstance(popoverTriggerEl);
            if (existingPopover) {
                (existingPopover as { dispose?: () => void }).dispose?.();
            }
            // Initialize new popover
            const popoverInstance = new Popover(popoverTriggerEl, {
                html: true,
                sanitize: true
            });
            popoverInstances.push(popoverInstance);
        });
    }
}
