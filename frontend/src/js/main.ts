/**
 * Main JavaScript entry point for What's the Damage v2 results page
 */

import $ from 'jquery';
import { initStatisticalAnalysis } from './statistical-analysis';

/**
 * DataTables configuration type extension
 * The DataTables types don't include all options, so we extend them
 */
interface DataTablesConfig {
    dom?: string;
    buttons?: string[];
    responsive?: boolean;
    pageLength?: number;
    [key: string]: unknown;
}

/**
 * Initialize DataTables on a specific table element
 */
function initDataTable(table: Element): void {
    // Check if DataTable is already initialized on this table
    if ($(table).hasClass('dataTable')) {
        $(table).DataTable().destroy();
    }

    $(table).DataTable({
        dom: 'Bfrtip',
        buttons: ['csv', 'excel'],
        responsive: true,
        pageLength: 25
    } as DataTablesConfig);
}

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
 * Initialize DataTables and Bootstrap components
 */
export function initMainPage(): void {
    // Initialize DataTables for all tables with data-datatable attribute
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    tables.forEach(initDataTable);

    // Initialize Bootstrap popovers with proper sanitization
    // Use globalThis.bootstrap which is set by src/main.ts
    const bootstrap = (globalThis as unknown as Window).bootstrap as WindowBootstrap | undefined;
    if (bootstrap?.Popover) {
        const Popover = bootstrap.Popover;
        const popoverTriggerList = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map((popoverTriggerEl: Element) => {
            // Destroy existing popover if it exists
            const existingPopover = Popover.getInstance(popoverTriggerEl);
            if (existingPopover) {
                (existingPopover as { dispose?: () => void }).dispose?.();
            }
            return new Popover(popoverTriggerEl, {
                html: true,
                sanitize: true
            });
        });
    }

    // Initialize statistical analysis if controls are present
    initStatisticalAnalysis();
}
