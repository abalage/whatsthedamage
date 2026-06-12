<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import {
  useDrilldownData,
  type BreadcrumbItem
} from '../composables/useDrilldownData.js'
import { useCategoriesStore } from '../stores/categories.js'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import { fetchCategoryMonthTransactions } from '../js/api.js'
import type { CategoryMonthTransactionsApiResponse } from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()


// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

// Table columns
const columns: Column[] = [
  { key: 'date', title: $gettext('Date'), renderHtml: (value: unknown, row: Record<string, unknown>) => String((row as { date_display?: string }).date_display || value || '') },
  {
    key: 'amount',
    title: $gettext('Amount'),
    renderHtml: (value: unknown, row: Record<string, unknown>) => String((row as { amount_display?: string }).amount_display || value || '')
  },
  { key: 'merchant', title: $gettext('Merchant') }
]

// Function to get page title with category display name
const getPageTitle = (data: CategoryMonthTransactionsApiResponse): string => {
  const categoryId = categoriesStore.extractCategoryIdFromData(data as Record<string, unknown>)
  const categoryDisplayName = categoryId ? categoriesStore.getCategoryDisplayName(categoryId) : ''
  return `${$gettext('Details')}: ${categoryDisplayName} - ${data.month_name}`
}

const {
  data: transactionsData,
  isLoading,
  error,
  fetchData,
  pageTitle,
  breadcrumbItems,
  navButtons
} = useDrilldownData<CategoryMonthTransactionsApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.categoryId || !params.monthId) {
      throw new Error('Missing required parameters for category month transactions fetch')
    }
    return fetchCategoryMonthTransactions(params)
  },
  getPageTitle,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Results'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    {
      name: $gettext('Category Months'),
      to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }
    },
    { name: $gettext('Transaction Details'), active: true }
  ],
  navButtons: [
    {
      text: $gettext('Back to Category Months'),
      to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } },
      variant: 'secondary'
    },
    {
      text: $gettext('Back to Categories'),
      to: { name: 'results', query: { resultId: getRouteParam('resultId') } },
      variant: 'outline-secondary'
    }
  ],
  errorMessageKey: 'transactionsLoadError'
})

// Table data
const tableData = computed(() => {
  if (!transactionsData.value) return []
  return transactionsData.value.data.map(t => ({
    date: typeof t.date.timestamp === 'string' ? Number(t.date.timestamp) : t.date.timestamp,
    date_display: t.date.display,
    amount: t.amount.raw,
    amount_display: t.amount.display,
    merchant: t.merchant,
    row_id: t.row_id
  }))
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

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-primary">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </output>
      <p class="mt-2">{{ $gettext('Loading data') }}...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="transactionsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ pageTitle }}</h1>
        <div v-if="navButtons && navButtons.length" class="d-flex gap-2">
          <ButtonComponent
            v-for="(button, index) in navButtons"
            :key="index"
            :text="button.text"
            :variant="button.variant"
            :to="button.to"
            :size="button.size"
            :class="index < navButtons.length - 1 ? 'mt-3 mb-3 me-2' : 'mt-3 mb-3'"
          />
        </div>
      </div>

      <!-- Account Card -->
      <CardComponent :title="transactionsData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-8 mb-3">
            <VueDataTable
              id="transaction-details-table"
              :data="tableData"
              :columns="columns"
              :csv-text="$gettext('Export CSV')"
              :excel-text="$gettext('Export Excel')"
              show-column-filters
            />
          </div>
        </div>
      </CardComponent>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
