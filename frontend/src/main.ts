import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './css/main.css'

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css'
import 'datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css'
import 'datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css'

// Create Vue app
const app = createApp(App)

// Use router
app.use(router)

// Mount the app
app.mount('#app')