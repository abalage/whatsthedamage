import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './css/main.css'
import './css/components.css'
import './css/results.css'

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css'
import 'datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css'
import 'datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css'

// Import DataTables JavaScript libraries
import $ from 'jquery'
import * as bootstrapNs from 'bootstrap'

// Assign jQuery and Bootstrap to window BEFORE importing DataTables
// This ensures DataTables can find jQuery as a global
window.$ = window.jQuery = $;
window.bootstrap = bootstrapNs.default ?? bootstrapNs;

// Import DataTables - these will use window.$ / window.jQuery
import 'datatables.net'
import 'datatables.net-bs5'
import 'datatables.net-buttons'
import 'datatables.net-buttons-bs5'
import 'datatables.net-fixedheader'
import 'datatables.net-fixedheader-bs5'

// Import JSZip and assign to window BEFORE importing buttons.html5
// buttons.html5.js requires window.JSZip to be set when it executes
import JSZip from 'jszip';
window.JSZip = JSZip;
import 'datatables.net-buttons/js/buttons.html5';

// Import DataTables initialization
import { initMainPage } from './js/main'
import { updateCellHighlights } from './js/statistical-analysis'

// Declare global window types
declare global {
  interface Window {
    exportCsvText: string
    exportExcelText: string
    bootstrap: Record<string, unknown>
    JSZip: unknown
    $: typeof import('jquery')
    jQuery: typeof import('jquery')
    initMainPage: () => void
    updateCellHighlights: (highlights: Record<string, string[]>) => void
  }
}

// Make initMainPage available globally for components
window.initMainPage = initMainPage;
window.updateCellHighlights = updateCellHighlights;

// Create Vue app
const app = createApp(App)

// Install Pinia
const pinia = createPinia()
app.use(pinia)

// Use router
app.use(router)

// Mount the app
app.mount('#app')