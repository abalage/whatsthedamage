/**
 * Main JavaScript entry point for What's the Damage v2 results page
 */

import $ from 'jquery';
import 'bootstrap';
import { initStatisticalAnalysis } from './statistical-analysis';

/**
 * Initialize DataTables on a specific table element
 */
function initDataTable(table: Element): void {
    // Check if DataTable is already initialized on this table
    if ($(table).hasClass('dataTable')) {
        // Destroy existing instance to allow reinitialization
        $(table).DataTable().destroy();
    }

    $(table).DataTable({
        responsive: true,
        fixedHeader: true,
        ordering: true,
        pageLength: 25,
        scrollX: false,
        autoWidth: true,
        dom: 'Bfrtip',
        buttons: [
            {
                extend: 'csv',
                text: window.exportCsvText || 'Export CSV',
                title: 'whatsthedamage_export'
            },
            {
                extend: 'excel',
                text: window.exportExcelText || 'Export Excel',
                title: 'whatsthedamage_export'
            }
        ]
    } as any);
}

/**
 * Initialize DataTables and Bootstrap components
 */
export function initMainPage(): void {
    // Initialize DataTables for all tables with data-datatable attribute
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    tables.forEach(initDataTable);

    // Initialize Bootstrap popovers with proper sanitization
    const popoverTriggerList = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl: Element) {
        // Destroy existing popover if it exists
        const existingPopover = window.bootstrap.Popover.getInstance(popoverTriggerEl);
        if (existingPopover) {
            existingPopover.dispose();
        }
        return new window.bootstrap.Popover(popoverTriggerEl, {
            html: true,
            sanitize: true
            // Note: allowList removed to avoid TypeScript errors
            // Bootstrap 5 handles basic sanitization automatically
        });
    });

    // Initialize statistical analysis if controls are present
    initStatisticalAnalysis();
}
