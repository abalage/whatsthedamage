<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical.js'
import { useCategoriesStore } from '../stores/categories.js'
import { useDrilldownData } from '../composables/useDrilldownData.js'
import { RouterLink } from 'vue-router'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs.js'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchAggregatedTransactions } from '../js/api.js'
import { buildResultQuery } from '../js/routeUtils.js'
import { useResultQuery } from '../composables/useResultQuery.js'
import type { AggregatedTransactionsResponse, TransactionListItem } from '../types/api.js'
import { formatMonthYear, extractMonthKey, createMonthDate } from '../js/dateUtils.js'
import BarChart from '../components/charts/BarChart.vue'

// Helper function to format amount with currency
function formatAmount(amount: number, currency: string | undefined): string {
  if (currency) {
    return `${currency} ${amount.toFixed(2)}`
  }
  return amount.toFixed(2)
}

const { $gettext } = useGettext()

const statisticalStore = useStatisticalStore()
const categoriesStore = useCategoriesStore()

// Optional resultId filter, carried in the query string
const resultQuery = useResultQuery()

// Table columns
const columns: Column[] = [
  {
    key: 'month',
    title: $gettext('Month'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const accountId = String(row?.accountId || '')
      const categoryId = String(row?.categoryId || '')
      const monthId = extractMonthIdFromData(row ?? {})
      return {
        to: {
          name: 'category-month-transactions',
          params: { accountId, categoryId, monthId },
          query: buildResultQuery(String(row?.resultId || ''))
        },
        class: 'clickable',
        children: String(value)
      }
    }
  },
  {
    key: 'total',
    title: $gettext('Total'),
    renderHtml: (value: unknown, row?: Record<string, unknown>) => String(((row as { total_display?: string })?.total_display) || value || '')
  }
]

// Extract month_id from row data
function extractMonthIdFromData(row: Record<string, unknown>): string {
  const rowId = row.row_id as string | undefined

  // Use row_id (which is the month key in YYYY-MM format) as the month_id
  if (rowId) {
    return rowId
  }

  // Fallback to month_timestamp if row_id is not available
  const monthTimestamp = row.month_timestamp as number | string | undefined
  return String(monthTimestamp || '')
}

const {
  data: categoryMonthsData,
  isLoading,
  error,
  fetchData,
  resultId,
  accountId,
  categoryId,
  pageTitle,
  breadcrumbItems
} = useDrilldownData<AggregatedTransactionsResponse>({
  fetchData: async (params) => {
    if (!params.accountId || !params.categoryId) {
      throw new Error('Missing required parameters for category months fetch')
    }
    return fetchAggregatedTransactions({
      result_id: params.resultId ?? undefined,
      account: params.accountId,
      category_id: params.categoryId,
      group_by: 'month'
    })
  },
  titleBaseKey: 'Category Details',
  titleFormat: 'category',
  titleExtractor: (data: AggregatedTransactionsResponse) => ({
    categoryId: data.category_id
  }),
  breadcrumbItems: (data: AggregatedTransactionsResponse | null): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Categories'), to: { name: 'results', query: resultQuery() } },
    { name: data ? categoriesStore.getCategoryDisplayName(data.category_id || '') : $gettext('Category Details'), active: true }
  ],
  errorMessageKey: 'categoryMonthsLoadError'
})

// Helper function to format month key (YYYY-MM) to display format
function formatMonthKey(monthKey: string): string {
  // monthKey is in YYYY-MM format
  const normalized = extractMonthKey(monthKey)
  const monthDate = createMonthDate(normalized)
  if (monthDate) {
    return formatMonthYear(monthDate.getTime() / 1000)
  }
  return monthKey
}

// Helper function to calculate total for a group of transactions
function calculateTotalForTransactions(txns: TransactionListItem[]): number {
  return txns.reduce((sum, txn) => sum + (txn.amount || 0), 0)
}

// Table data
const tableData = computed(() => {
  if (!categoryMonthsData.value) return []

  const groups = categoryMonthsData.value.groups || {}

  return Object.entries(groups).map(([monthKey, txns]) => {
    const total = calculateTotalForTransactions(txns)
    const normalizedMonthKey = extractMonthKey(monthKey)
    const monthDate = createMonthDate(normalizedMonthKey)
    const monthTimestamp = monthDate ? monthDate.getTime() / 1000 : 0

    return {
      month: formatMonthKey(monthKey),
      total: total,
      total_display: formatAmount(total, txns[0]?.currency),
      row_id: normalizedMonthKey,
      cell_url: `#`,
      month_timestamp: monthTimestamp,
      resultId: resultId.value,
      accountId: accountId.value,
      categoryId: categoryId.value,
      _rowIds: {
        total: normalizedMonthKey
      }
    }
  })
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!categoryMonthsData.value || !categoryMonthsData.value.groups || Object.keys(categoryMonthsData.value.groups).length === 0) return []

  return [
    {
      id: 'total-sum',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold bg-surface-primary text-on-primary',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'month') return $gettext('Total')
        if (columnKey === 'total') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.reduce((sum, val) => sum + val, 0)
        }
        return ''
      }
    },
    {
      id: 'total-average',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold bg-surface-secondary text-on-dark',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'month') return $gettext('Average')
        if (columnKey === 'total') {
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

// Cell highlights from Pinia store
const cellHighlightsByRowId = computed(() => {
  return statisticalStore.highlights || {}
})

// Initialize highlights from API when data loads
watch(() => categoryMonthsData.value, (newData) => {
  if (newData?.highlights) {
    statisticalStore.setHighlights(newData.highlights)
  }
}, { immediate: true })

// Chart data for BarChart
const chartData = computed(() => {
  return tableData.value.map(row => ({
    label: row.month,
    timestamp: row.month_timestamp as number,
    values: { total: row.total as number }
  }))
})

const chartCategories = computed(() => [
  { id: 'total', label: $gettext('Amount') }
])

onMounted(() => {
  fetchData()
})

// Refetch when the resultId query filter changes while the page is reused
watch(resultId, () => {
  fetchData()
})
</script>

<template>
  <div class="container-fluid">
    <BreadcrumbNavigation :items="breadcrumbItems" />

    <LoadingState v-if="isLoading" />

    <ErrorState v-else-if="error" :message="error" />

    <!-- Main Content -->
    <div v-else-if="categoryMonthsData">
      <PageHeader :title="pageTitle">
        <template #actions>
          <RouterLink
            :to="{ name: 'results', query: buildResultQuery(resultId) }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Back to Categories') }}
          </RouterLink>
        </template>
      </PageHeader>

      <!-- Cards Container -->
      <div class="d-flex gap-4 flex-wrap justify-content-center">
        <!-- Account & Table Card -->
        <div class="card flex-grow-1" style="min-width: 400px">
          <div class="card-header">
            {{ $gettext('Account') }}: {{ accountId || $gettext('Unknown') }}
            <span v-if="categoryMonthsData?.account" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
              {{ categoryMonthsData?.account }}
            </span>
          </div>
          <div class="card-body">
            <VueDataTable
              id="datatable-category"
              :data="tableData"
              :columns="columns"
              :aggregate-rows="aggregateRows"
              :cell-highlights-by-row-id="cellHighlightsByRowId"
              :csv-text="$gettext('Export CSV')"
              :excel-text="$gettext('Export Excel')"
              wrapper-class="w-auto"
              show-column-filters
              show-pagination
            />
          </div>
        </div>

        <!-- Chart Card -->
        <div class="card flex-grow-1" style="min-width: 400px">
          <div class="card-header">
            {{ $gettext('Category Details') }}
          </div>
          <div class="card-body" style="height: 450px">
            <BarChart
              :data="chartData"
              :categories="chartCategories"
              show-trendline
            />
          </div>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No data available') }}
    </div>
  </div>
</template>
