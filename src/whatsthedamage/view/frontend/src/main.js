/**
 * Main entry point for What's the Damage frontend
 * Imports and initializes all modules
 */

// Import CSS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css';
import 'datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css';
import 'datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css';

// Import JS dependencies
import $ from 'jquery';
import * as bootstrap from 'bootstrap';
import 'datatables.net';
import 'datatables.net-bs5';
import 'datatables.net-fixedheader';
import 'datatables.net-buttons';
import 'datatables.net-buttons/js/buttons.html5.min';
import 'datatables.net-buttons/js/buttons.print.min';

// IMMEDIATELY set globals before anything else
globalThis.$ = $;
globalThis.jQuery = $;
globalThis.bootstrap = bootstrap;

// Import application modules and their init functions
import { initMainPage } from './js/main';
import { initStatisticalAnalysis } from './js/statistical-analysis';
import { clearForm } from './js/index';
import './js/utils';

// Make functions available globally for template usage
globalThis.clearForm = clearForm;

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
