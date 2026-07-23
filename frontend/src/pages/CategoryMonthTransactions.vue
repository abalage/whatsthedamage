<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useCategoriesStore } from '../stores/categories.js'
import { useDrilldownData } from '../composables/useDrilldownData.js'
import { useRoute, RouterLink } from 'vue-router'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs.js'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchCategoryMonthTransactions } from '../js/api.js'
import type { CategoryMonthTransactionsApiResponse } from '../types/api.js'
import { formatMonthYear } from '../js/dateUtils.js'

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
  { key: 'date', title: $gettext('Date'), renderHtml: (value: unknown, row?: Record<string, unknown>) => String(((row as { date_display?: string })?.date_display) || value || '') },
  {
    key: 'amount',
    title: $gettext('Amount'),
    renderHtml: (value: unknown, row?: Record<string, unknown>) => String(((row as { amount_display?: string })?.amount_display) || value || '')
  },
  { key: 'merchant', title: $gettext('Merchant') }
]

const {
  data: transactionsData,
  isLoading,
  error,
  fetchData,
  pageTitle,
  breadcrumbItems
} = useDrilldownData<CategoryMonthTransactionsApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.categoryId || !params.monthId) {
      throw new Error('Missing required parameters for category month transactions fetch')
    }
    return fetchCategoryMonthTransactions(params)
  },
  titleBaseKey: 'Transactions',
  titleFormat: 'category-month',
  titleExtractor: (data: CategoryMonthTransactionsApiResponse) => ({
    categoryId: categoriesStore.extractCategoryIdFromData(data as unknown as Record<string, unknown>),
    monthTimestamp: data.month_timestamp
  }),
  breadcrumbItems: (data: CategoryMonthTransactionsApiResponse | null): BreadcrumbItem[] => {
    const categoryName = data ? categoriesStore.getCategoryDisplayName(categoriesStore.extractCategoryIdFromData(data as unknown as Record<string, unknown>)) : null
    const monthName = data ? formatMonthYear(data.month_timestamp) : null
    return [
      { name: $gettext('Home'), to: '/' },
      { name: $gettext('Categories'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
      {
        name: $gettext('Category Months'),
        to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }
      },
      { name: categoryName && monthName ? `${categoryName} - ${monthName}` : $gettext('Transaction Details'), active: true }
    ]
  },
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

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!transactionsData.value || transactionsData.value.data.length === 0) return []

  return [
    {
      id: 'amount-sum',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold bg-surface-primary text-on-primary',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'date') return $gettext('Total')
        if (columnKey === 'amount') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.reduce((sum, val) => sum + val, 0)
        }
        return ''
      }
    },
    {
      id: 'amount-average',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold bg-surface-secondary text-on-dark',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'date') return $gettext('Average')
        if (columnKey === 'amount') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.length > 0
            ? numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length
            : null
        }
        return ''
      }
    }
  ]
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="container-fluid">
    <BreadcrumbNavigation :items="breadcrumbItems" />

    <LoadingState v-if="isLoading" />

    <ErrorState v-else-if="error" :message="error" />

    <!-- Main Content -->
    <div v-else-if="transactionsData">
      <PageHeader :title="pageTitle">
        <template #actions>
          <div class="d-flex gap-2">
            <RouterLink
              :to="{ name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }"
              class="btn bg-surface-base text-secondary border-secondary hover-bg-surface-secondary mt-3 mb-3"
            >
              {{ $gettext('Back to Category Months') }}
            </RouterLink>
            <RouterLink
              :to="{ name: 'results', query: { resultId: getRouteParam('resultId') } }"
              class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
            >
              {{ $gettext('Back to Categories') }}
            </RouterLink>
          </div>
        </template>
      </PageHeader>

      <!-- Account Card -->
      <div class="card mb-4" style="width: fit-content; margin: 0 auto">
        <div class="card-header">
          {{ $gettext('Account') }}: {{ transactionsData.account_formatted_id }}
          <span v-if="transactionsData.account_currency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
            {{ transactionsData.account_currency }}
          </span>
        </div>
        <div class="card-body">
          <VueDataTable
            id="transaction-details-table"
            :data="tableData"
            :columns="columns"
            :aggregate-rows="aggregateRows"
            :csv-text="$gettext('Export CSV')"
            :excel-text="$gettext('Export Excel')"
            wrapper-class="w-auto"
            show-column-filters
            show-pagination
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
