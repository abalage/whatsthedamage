<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical.js'
import { useCategoriesStore } from '../stores/categories.js'
import { useDrilldownData } from '../composables/useDrilldownData.js'
import { useRoute, RouterLink } from 'vue-router'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs.js'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import PieChart from '../components/charts/PieChart.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchMonthCategories } from '../js/api.js'
import { useResultQuery } from '../composables/useResultQuery.js'
import type { AggregatedTransactionsResponse, TransactionListItem } from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()
const statisticalStore = useStatisticalStore()

// Optional resultId filter, carried in the query string
const resultQuery = useResultQuery()

// Import formatMonthYear and date utilities for breadcrumb
import { formatMonthYear, createMonthDate } from '../js/dateUtils.js'

// Table columns
const columns: Column[] = [
  {
    key: 'category_id',
    title: $gettext('Category'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const accountId = String(route.params.accountId || '')
      const monthId = String(route.params.monthId || '')
      const categoryId = extractCategoryIdFromData(row ?? {})
      const categoryDisplayName = categoriesStore.getCategoryDisplayName(String(row?.category_id ?? ''))
      return {
        to: {
          name: 'category-month-transactions',
          params: { accountId, categoryId, monthId },
          query: resultQuery()
        },
        class: 'clickable',
        children: categoryDisplayName
      }
    }
  },
  {
    key: 'total',
    title: $gettext('Total'),
    renderHtml: (value: unknown, row?: Record<string, unknown>) => String(((row as { total_display?: string })?.total_display) || value || '')
  }
]

// Extract category_id from row data
function extractCategoryIdFromData(row: Record<string, unknown>): string {
  const category_id = row.category_id as string | undefined
  const categoryUrl = row.category_url as string | undefined
  if (categoryUrl) {
    const match = categoryUrl.match(/categories\/([^/]+)\/months/)
    if (match) return match[1]
  }
  return category_id || ''
}

const {
  data: monthCategoriesData,
  isLoading,
  error,
  fetchData,
  resultId,
  pageTitle,
  breadcrumbItems,
  accountId
} = useDrilldownData<AggregatedTransactionsResponse>({
  fetchData: async (params) => {
    if (!params.accountId || !params.monthId) {
      throw new Error('Missing required parameters for month categories fetch')
    }
    return fetchMonthCategories(params)
  },
  titleBaseKey: 'Month Details',
  titleFormat: 'month',
  titleExtractor: (data: AggregatedTransactionsResponse) => {
    const monthDate = createMonthDate(data.month || '')
    return { monthTimestamp: monthDate ? monthDate.getTime() / 1000 : 0 }
  },
  breadcrumbItems: (data: AggregatedTransactionsResponse | null): BreadcrumbItem[] => {
    const monthDate = data ? createMonthDate(data.month || '') : null
    const monthName = monthDate ? formatMonthYear(monthDate.getTime() / 1000) : $gettext('Month Details')
    return [
      { name: $gettext('Home'), to: '/' },
      { name: $gettext('Categories'), to: { name: 'results', query: resultQuery() } },
      { name: monthName, active: true }
    ]
  },
  errorMessageKey: 'monthCategoriesLoadError'
})



// Helper function to calculate total for a group of transactions
function calculateTotalForTransactions(txns: TransactionListItem[]): number {
  return txns.reduce((sum, txn) => sum + (txn.amount || 0), 0)
}

// Helper function to format amount with currency
function formatAmount(amount: number, currency: string | undefined): string {
  if (currency) {
    return `${currency} ${amount.toFixed(2)}`
  }
  return amount.toFixed(2)
}

// Extract account currency from first transaction
const accountCurrency = computed(() => {
  if (!monthCategoriesData.value?.groups) return null
  const groups = monthCategoriesData.value.groups
  for (const txns of Object.values(groups)) {
    if (txns.length > 0 && txns[0].currency) {
      return txns[0].currency
    }
  }
  return null
})

// Table data with _rowIds mapping
const tableData = computed(() => {
  if (!monthCategoriesData.value) return []
  const groups = monthCategoriesData.value.groups || {}

  return Object.entries(groups).map(([categoryKey, txns]) => {
    const total = calculateTotalForTransactions(txns)
    const firstTxn = txns[0]
    return {
      category_id: categoryKey,
      total: total,
      total_display: formatAmount(total, firstTxn?.currency),
      row_id: categoryKey,
      _rowIds: {
        total: categoryKey // Map total column to its row_id for cell-level highlighting
      }
    }
  })
})

// Pie chart data for category distribution visualization
const pieChartData = computed(() => {
  if (!monthCategoriesData.value) return []
  const groups = monthCategoriesData.value.groups || {}
  return Object.entries(groups).map(([categoryKey, txns]) => {
    const total = calculateTotalForTransactions(txns)
    return {
      label: categoriesStore.getCategoryDisplayName(categoryKey),
      value: total,
      categoryId: categoryKey
    }
  })
})

// Total sum for pie chart display
const totalSum = computed(() => {
  if (!monthCategoriesData.value) return 0
  const groups = monthCategoriesData.value.groups || {}
  return Object.values(groups).reduce((sum, txns) => {
    return sum + calculateTotalForTransactions(txns)
  }, 0)
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!monthCategoriesData.value || !monthCategoriesData.value.groups || Object.keys(monthCategoriesData.value.groups).length === 0) return []

  return [
    {
      id: 'total-sum',
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      class: 'fw-bold bg-surface-primary text-on-primary',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'category_id') return $gettext('Total')
        if (columnKey === 'total') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.reduce((sum, val) => sum + val, 0)
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
// Note: The aggregate endpoint returns statistical data, not highlight types
// So we don't set highlights here - they should come from the main results endpoint
watch(() => monthCategoriesData.value, () => {
  // Clear highlights for this drilldown view
  statisticalStore.setHighlights({})
}, { immediate: true })

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
    <div v-else-if="monthCategoriesData">
      <PageHeader :title="pageTitle">
        <template #actions>
          <RouterLink
            :to="{ name: 'results', query: resultQuery() }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Back to Categories') }}
          </RouterLink>
        </template>
      </PageHeader>

      <!-- Cards Container -->
      <div class="d-flex flex-wrap gap-4 justify-content-center mb-4">
        <!-- Account Card -->
        <div class="card" style="width: fit-content; flex: 1; min-width: 400px">
          <div class="card-header">
            {{ $gettext('Account') }}: {{ accountId || $gettext('Unknown') }}
            <span v-if="accountCurrency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
              {{ accountCurrency }}
            </span>
          </div>
          <div class="card-body">
            <VueDataTable
              id="datatable-month"
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

        <!-- Category Distribution Chart Card -->
        <div class="card" style="width: fit-content; flex: 1; min-width: 400px">
          <div class="card-header">
            {{ $gettext('Category Distribution') }}
          </div>
          <div class="card-body">
            <PieChart
              :data="pieChartData"
              :total="totalSum"
              :showLegend="true"
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
