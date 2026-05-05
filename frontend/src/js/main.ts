/**
 * Main JavaScript entry point for What's the Damage v2 results page
 */

import $ from 'jquery';
import { initStatisticalAnalysis } from './statistical-analysis';

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
    });
}

/**
 * Initialize DataTables and Bootstrap components
 */
export function initMainPage(): void {
    // Initialize DataTables for all tables with data-datatable attribute
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    tables.forEach(initDataTable);

    // Initialize Bootstrap popovers with proper sanitization
    // Use window.bootstrap which is set by src/main.ts
    const bootstrap = (window as any).bootstrap;
    if (bootstrap?.Popover) {
        const popoverTriggerList = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl: Element) {
            // Destroy existing popover if it exists
            const existingPopover = bootstrap.Popover.getInstance(popoverTriggerEl);
            if (existingPopover) {
                existingPopover.dispose();
            }
            return new bootstrap.Popover(popoverTriggerEl, {
                html: true,
                sanitize: true
            });
        });
    }

    // Initialize statistical analysis if controls are present
    initStatisticalAnalysis();
}
