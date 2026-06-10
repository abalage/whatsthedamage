import { createApp, type Plugin } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'

// Import custom CSS (after Bootstrap to ensure proper override)
import './css/main.css'

// Import and install gettext
import gettext from './js/gettext.js'

// Import Bootstrap for popover support
import * as bootstrapNs from 'bootstrap'

// Assign Bootstrap to globalThis for popover initialization
declare global {
  interface Window {
    bootstrap: unknown
  }
}
(globalThis as unknown as Window).bootstrap = bootstrapNs

// Import and register popover directive
import { popoverDirective } from './directives/popover.js'

// Create Vue app
const app = createApp(App)

// Install Pinia
const pinia = createPinia()
app.use(pinia)

// Install vue3-gettext
app.use(gettext as unknown as Plugin)

// Use router
app.use(router)

// Register global directives
app.directive('popover', popoverDirective)

// Mount the app
app.mount('#app')
