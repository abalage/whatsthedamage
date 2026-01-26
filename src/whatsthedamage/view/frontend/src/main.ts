/**
 * Main entry point for What's the Damage frontend
 * Imports and initializes all modules
 */

// Declare global window extensions for Bootstrap and jQuery
declare global {
    interface Window {
        bootstrap: any;
        $: any;
        jQuery: any;
    }
}

// Import CSS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css';
import 'datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css';
import 'datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css';

// Import JS dependencies
import $ from 'jquery';
import * as bootstrap from 'bootstrap';
// Expose Bootstrap to global window object for popovers
window.bootstrap = bootstrap;
// Expose jQuery to global window object
window.$ = $;
window.jQuery = $;
// Import JSZip BEFORE buttons.html5 for Excel export functionality
import JSZip from 'jszip';
// Expose JSZip to global window object for DataTables buttons
(globalThis as any).JSZip = JSZip;
import 'datatables.net';
import 'datatables.net-bs5';
import 'datatables.net-fixedheader';
import 'datatables.net-buttons';
import 'datatables.net-buttons-bs5';
import 'datatables.net-buttons/js/buttons.html5.min';
import 'datatables.net-buttons/js/buttons.print.min';

// Import application modules and their init functions
import { initMainPage } from './js/main';
import { initStatisticalAnalysis } from './js/statistical-analysis';

// Initialize all modules when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initMainPage();
        initStatisticalAnalysis();
    });
} else {
    // DOM already loaded
    initMainPage();
    initStatisticalAnalysis();
}

// Export for use in other modules
export { default as $ } from 'jquery';
export { clearForm } from './js/index';
export { initMainPage } from './js/main';
export { initStatisticalAnalysis } from './js/statistical-analysis';
