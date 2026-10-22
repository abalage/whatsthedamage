import { createRouter, createWebHistory } from 'vue-router'
import Index from '../pages/Index.vue'
import About from '../pages/About.vue'
import Legal from '../pages/Legal.vue'
import Privacy from '../pages/Privacy.vue'
import NotFound from '../pages/NotFound.vue'
import Categories from '../pages/Categories.vue'
import Transactions from '../pages/Transactions.vue'
import Statistics from '../pages/Statistics.vue'
import CategoryMonthsList from '../pages/CategoryMonthsList.vue'
import MonthCategoriesList from '../pages/MonthCategoriesList.vue'
import CategoryMonthTransactions from '../pages/CategoryMonthTransactions.vue'
import PivotTable from '../pages/PivotTable.vue'
import Login from '../pages/Login.vue'
import Register from '../pages/Register.vue'
import ForgotPassword from '../pages/ForgotPassword.vue'
import Logout from '../pages/Logout.vue'
import Import from '../pages/Import.vue'
import Settings from '../pages/Settings.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'index',
      component: Index,
      meta: { requiresAuth: true }
    },
    {
      path: '/import',
      name: 'import',
      component: Import,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
      meta: { requiresAuth: true }
    },
    {
      path: '/about',
      name: 'about',
      component: About,
      meta: { public: true }
    },
    {
      path: '/legal',
      name: 'legal',
      component: Legal,
      meta: { public: true }
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: Privacy,
      meta: { public: true }
    },
    {
      path: '/results',
      name: 'results',
      component: Categories,
      meta: { requiresAuth: true }
    },
    {
      path: '/results/accounts/:accountId/categories/:categoryId/months',
      name: 'category-months',
      component: CategoryMonthsList,
      meta: { requiresAuth: true }
    },
    {
      path: '/results/accounts/:accountId/months/:monthId/categories',
      name: 'month-categories',
      component: MonthCategoriesList,
      meta: { requiresAuth: true }
    },
    {
      path: '/results/accounts/:accountId/categories/:categoryId/months/:monthId/transactions',
      name: 'category-month-transactions',
      component: CategoryMonthTransactions,
      meta: { requiresAuth: true }
    },
    {
      path: '/transactions',
      name: 'details',
      component: Transactions,
      meta: { requiresAuth: true }
    },
    {
      path: '/pivot',
      name: 'pivot',
      component: PivotTable,
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: Statistics,
      meta: { requiresAuth: true }
    },
    // Authentication routes
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { requiresGuest: true, public: true }
    },
    {
      path: '/register',
      name: 'register',
      component: Register,
      meta: { requiresGuest: true, public: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPassword,
      meta: { requiresGuest: true, public: true }
    },
    {
      path: '/logout',
      name: 'logout',
      component: Logout,
      meta: { public: true }
    },
    // Catch-all: 404 page for unknown paths (including removed legacy URLs)
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFound,
      meta: { public: true }
    }
  ]
});

// Navigation guards for authentication
router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Restore the session from cookies on the first navigation. This runs
  // for public routes too, so requiresGuest redirects and login-state
  // aware pages work without each page re-initializing the store.
  if (!authStore.isInitialized && !authStore.isLoading) {
    await authStore.initialize();
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Save the route the user was trying to visit for redirect after login
    return {
      name: 'login',
      query: { redirect: to.fullPath }
    };
  }

  // Check if route requires guest (not authenticated)
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return { name: 'index' };
  }

  // Default: allow navigation
  return true;
});

export default router
