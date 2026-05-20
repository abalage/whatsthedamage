<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import {
  useDrilldownData,
  type BreadcrumbItem
} from '../composables/useDrilldownData'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import StatisticalControls from '../components/ui/StatisticalControls.vue'
import { fetchCategoryMonthTransactions } from '../js/api'
import type { CategoryMonthTransactionsResponse } from '../types/api'

const localeStore = useLocaleStore()
const route = useRoute()

const t = (key: string) => getTranslation(key, localeStore.locale)

// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

const {
  data: transactionsData,
  isLoading,
  error,
  fetchData,
  resultId,
  pageTitle,
  breadcrumbItems,
  navButtons
} = useDrilldownData<CategoryMonthTransactionsResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.categoryId || !params.monthId) {
      throw new Error('Missing required parameters for category month transactions fetch')
    }
    return fetchCategoryMonthTransactions(params)
  },
  getPageTitle: (data) => `${t('Transaction Details')}: ${data.category_name} - ${data.month_name}`,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: t('Home'), to: '/' },
    { name: t('Results'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    {
      name: t('Category Months'),
      to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }
    },
    { name: t('Transaction Details'), active: true }
  ],
  navButtons: [
    {
      text: t('Back to Category Months'),
      to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } },
      variant: 'secondary'
    },
    {
      text: t('Back to Results'),
      to: { name: 'results', query: { resultId: getRouteParam('resultId') } },
      variant: 'outline-secondary'
    }
  ],
  onDataLoaded: (data) => {
    // Set translation strings for DataTables export buttons
    window.exportCsvText = t('Export CSV')
    window.exportExcelText = t('Export Excel')

    // Set highlights for statistical cell highlighting
    window.highlights = data.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
  },
  errorMessageKey: 'transactionsLoadError'
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="container">
    <!-- Breadcrumb Navigation -->
    <nav v-if="breadcrumbItems.length" aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li
          v-for="(item, index) in breadcrumbItems"
          :key="index"
          class="breadcrumb-item"
          :class="{ 'active': item.active }"
          :aria-current="item.active ? 'page' : undefined"
        >
          <router-link v-if="item.to && !item.active" :to="item.to">{{ item.name }}</router-link>
          <span v-else>{{ item.name }}</span>
        </li>
      </ol>
    </nav>

    <StatisticalControls v-if="transactionsData" :result-id="resultId" />

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ t('loading') }}...</span>
      </div>
      <p class="mt-2">{{ t('loadingData') }}...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="transactionsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ pageTitle }}</h1>
      </div>

      <!-- Account Card -->
      <CardComponent :title="transactionsData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-8 mb-3">
            <div class="table-responsive">
              <table id="transaction-details-table" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Date') }}</th>
                    <th>{{ t('Amount') }}</th>
                    <th>{{ t('Merchant') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="transaction in transactionsData.data" :key="transaction.row_id">
                    <td>{{ transaction.date.display }}</td>
                    <td :data-row-id="transaction.row_id" class="">
                      {{ transaction.amount.display }}
                    </td>
                    <td>{{ transaction.merchant }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </CardComponent>

      <!-- Navigation -->
      <div v-if="navButtons && navButtons.length" class="row">
        <div class="col-md-6">
          <ButtonComponent
            v-for="(button, index) in navButtons"
            :key="index"
            :text="button.text"
            :variant="button.variant"
            :to="button.to"
            :size="button.size"
            class="mt-3 mb-3 me-2"
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ t('noTransactionsFound') }}
    </div>
  </div>
</template>

<style scoped>
/* Component-specific styles can be added here */
</style>
