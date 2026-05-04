import { createApp, nextTick } from 'vue'
import App from './App.vue'
import router from './router'
import './css/main.css'

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css'
import 'datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css'
import 'datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css'

// Import DataTables JavaScript libraries
import $ from 'jquery'
import 'bootstrap'
import 'datatables.net'
import 'datatables.net-bs5'
import 'datatables.net-buttons'
import 'datatables.net-buttons-bs5'
import 'datatables.net-fixedheader'
import 'datatables.net-fixedheader-bs5'

// Import DataTables initialization
import { initMainPage } from './js/main'

// Declare global window types
declare global {
  interface Window {
    exportCsvText: string
    exportExcelText: string
    bootstrap: any
  }
}

// Create Vue app
const app = createApp(App)

// Use router
app.use(router)

// Mount the app
app.mount('#app')

// Note: DataTables initialization is now handled per-component
// to support dynamic content loading (e.g., Results.vue after API fetch)