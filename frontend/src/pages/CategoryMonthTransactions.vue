<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useCategoriesStore } from '../stores/categories.js'
import {
  useDrilldownData,
  type BreadcrumbItem
} from '../composables/useDrilldownData.js'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
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
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Categories'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    {
      name: $gettext('Category Months'),
      to: { name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }
    },
    { name: $gettext('Transaction Details'), active: true }
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

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!transactionsData.value || transactionsData.value.data.length === 0) return []

  return [
    {
      id: 'amount-sum',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold table-light',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'date') return $gettext('Total')
        if (columnKey === 'amount') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.reduce((sum, val) => sum + val, 0)
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
          <ButtonComponent
            :text="$gettext('Back to Category Months')"
            :to="{ name: 'category-months', params: { resultId: getRouteParam('resultId'), accountId: getRouteParam('accountId'), categoryId: getRouteParam('categoryId') } }"
            variant="outline-secondary"
            class="mt-3 mb-3"
          />
          <ButtonComponent
            :text="$gettext('Back to Categories')"
            :to="{ name: 'results', query: { resultId: getRouteParam('resultId') } }"
            variant="secondary"
            class="mt-3 mb-3"
          />
          </div>
        </template>
      </PageHeader>

      <!-- Account Card -->
      <CardComponent type="account" :account="{ id: transactionsData.account_id, name: transactionsData.account_name, formatted_id: transactionsData.account_formatted_id, currency: transactionsData.account_currency }" class="mb-4" width="fit-content">
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
      </CardComponent>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
