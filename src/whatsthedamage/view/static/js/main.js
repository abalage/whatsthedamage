/**
 * Main JavaScript entry point for What's the Damage v2 results page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables for all tables with data-datatable attribute
    var tables = document.querySelectorAll('table[data-datatable="true"]');
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
                    text: window.exportCsvText,
                    title: 'whatsthedamage_export'
                },
                {
                    extend: 'excel',
                    text: window.exportExcelText,
                    title: 'whatsthedamage_export'
                }
            ]
        });
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true,
            sanitize: false
        });
    });
});
