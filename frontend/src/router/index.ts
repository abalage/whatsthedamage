import { createRouter, createWebHistory } from 'vue-router'
import Index from '../pages/Index.vue'
import About from '../pages/About.vue'
import Legal from '../pages/Legal.vue'
import Privacy from '../pages/Privacy.vue'
import Results from '../pages/Results.vue'
import Details from '../pages/Details.vue'
import Statistics from '../pages/Statistics.vue'
import CategoryMonthsList from '../pages/CategoryMonthsList.vue'
import MonthCategoriesList from '../pages/MonthCategoriesList.vue'
import CategoryMonthTransactions from '../pages/CategoryMonthTransactions.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'index',
      component: Index
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
      component: Results
    },
    {
      path: '/results/:resultId/accounts/:accountId/categories/:categoryId/months',
      name: 'category-months',
      component: CategoryMonthsList
    },
    {
      path: '/results/:resultId/accounts/:accountId/months/:monthId/categories',
      name: 'month-categories',
      component: MonthCategoriesList
    },
    {
      path: '/results/:resultId/accounts/:accountId/categories/:categoryId/months/:monthId/transactions',
      name: 'category-month-transactions',
      component: CategoryMonthTransactions
    },
    {
      path: '/results/:resultId/details',
      name: 'details',
      component: Details
    },
    {
      path: '/details',
      name: 'details-legacy',
      redirect: { name: 'index' } // Redirect legacy route
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: Statistics
    }
  ]
})

export default router