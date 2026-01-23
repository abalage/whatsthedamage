/**
 * Main JavaScript entry point for What's the Damage v2 results page
 */

import $ from 'jquery';
import 'bootstrap';

/**
 * Initialize DataTables and Bootstrap components
 */
export function initMainPage() {
    // Initialize DataTables for all tables with data-datatable attribute
    const tables = document.querySelectorAll('table[data-datatable="true"]');
        tables.forEach(function(table) {
            $(table).DataTable({
                responsive: false,
                fixedHeader: true,
                order: [],
                pageLength: 25,
                scrollX: true,
                autoWidth: false,
                dom: 'Bfrtip',
                buttons: [
                    {
                        extend: 'csv',
                        text: globalThis.exportCsvText,
                        title: 'whatsthedamage_export'
                    },
                    {
                        extend: 'excel',
                        text: globalThis.exportExcelText,
                        title: 'whatsthedamage_export'
                    }
                ]
            });
        });

    // Initialize Bootstrap popovers
    const popoverTriggerList = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true,
            sanitize: false
        });
    });
}
