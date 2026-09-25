import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import Index from '../pages/Index.vue'
import About from '../pages/About.vue'
import Legal from '../pages/Legal.vue'
import Privacy from '../pages/Privacy.vue'
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
import Import from '../pages/Import.vue'
import { useAuthStore } from '../stores/auth.js'

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
      path: '/about',
      name: 'about',
      component: About
    },
    {
      path: '/legal',
      name: 'legal',
      component: Legal
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: Privacy
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
    // Legacy result_id path-based routes, kept as redirects for backward compatibility
    {
      path: '/results/:resultId',
      redirect: to => ({ name: 'details', query: { resultId: String(to.params.resultId) } })
    },
    {
      path: '/results/:resultId/pivot',
      redirect: to => ({ name: 'pivot', query: { resultId: String(to.params.resultId) } })
    },
    {
      path: '/results/:resultId/accounts/:accountId/categories/:categoryId/months',
      redirect: to => ({
        name: 'category-months',
        params: { accountId: String(to.params.accountId), categoryId: String(to.params.categoryId) },
        query: { resultId: String(to.params.resultId) }
      })
    },
    {
      path: '/results/:resultId/accounts/:accountId/months/:monthId/categories',
      redirect: to => ({
        name: 'month-categories',
        params: { accountId: String(to.params.accountId), monthId: String(to.params.monthId) },
        query: { resultId: String(to.params.resultId) }
      })
    },
    {
      path: '/results/:resultId/accounts/:accountId/categories/:categoryId/months/:monthId/transactions',
      redirect: to => ({
        name: 'category-month-transactions',
        params: {
          accountId: String(to.params.accountId),
          categoryId: String(to.params.categoryId),
          monthId: String(to.params.monthId)
        },
        query: { resultId: String(to.params.resultId) }
      })
    },
    {
      path: '/details',
      name: 'details-legacy',
      redirect: { name: 'index' } // Redirect legacy route
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
      component: Login,
      beforeEnter: async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
        const authStore = useAuthStore();
        try {
          await authStore.logout();
        } finally {
          next({ name: 'login', query: { loggedOut: 'true' } });
        }
      },
      meta: { public: true }
    }
  ]
});

// Navigation guards for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // Initialize auth state if not already done
  // Only initialize for routes that might need auth (not for public routes like login/register)
  if (!to.meta.public && !authStore.isAuthenticated && !authStore.isLoading) {
    try {
      await authStore.initialize();
    } catch {
      // Initialization failed - not authenticated
    }
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Save the route the user was trying to visit for redirect after login
    next({
      name: 'login',
      query: { redirect: to.fullPath }
    });
    return;
  }

  // Check if route requires guest (not authenticated)
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'index' });
    return;
  }

  // Default: allow navigation
  next();
});

// Add public meta to routes that don't have explicit auth configuration
const routes = router.getRoutes();
routes.forEach(route => {
  if (!route.meta.public && !route.meta.requiresAuth && !route.meta.requiresGuest) {
    // Routes without explicit auth meta are public by default
    route.meta.public = true;
  }
});

export default router
