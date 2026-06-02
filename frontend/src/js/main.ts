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
    buttons?: Array<{
        extend: string;
        text?: string;
        className?: string;
        [key: string]: unknown;
    }>;
    responsive?: boolean;
    pageLength?: number;
    language?: {
        buttons?: {
            csv?: string;
            excel?: string;
        };
    };
    [key: string]: unknown;
}

/**
 * Initialize DataTables on a specific table element
 */
function initDataTable(table: Element, csvText?: string, excelText?: string): void {
    // Check if DataTable is already initialized on this table
    if ($(table).hasClass('dataTable')) {
        $(table).DataTable().destroy();
    }

    const config: DataTablesConfig = {
        dom: '<"dt-buttons"B><"clear">frtip',
        buttons: [
            {
                extend: 'csvHtml5',
                text: csvText || 'CSV',
                className: 'btn'
            },
            {
                extend: 'excelHtml5',
                text: excelText || 'Excel',
                className: 'btn'
            }
        ],
        responsive: true,
        pageLength: 25
    };

    $(table).DataTable(config);
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
 * Global storage for popover instances - allows bulk operations if needed
 */
let popoverInstances: unknown[] = [];

/**
 * Initialize DataTables and Bootstrap components
 */
export function initMainPage(): void {
    // Get export button text from global variables (set by Vue components)
    const windowObj = globalThis as unknown as Window;
    const csvText = windowObj.exportCsvText;
    const excelText = windowObj.exportExcelText;

    // Initialize DataTables for all tables with data-datatable attribute
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    tables.forEach(table => initDataTable(table, csvText, excelText));

    // Initialize Bootstrap popovers with proper sanitization
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

    // Initialize statistical analysis if controls are present
    initStatisticalAnalysis();
}


