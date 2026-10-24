<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical'
import { useCategoriesStore } from '../stores/categories'
import { useDrilldownData } from '../composables/useDrilldownData'
import {
  buildGroupRows,
  calculateTotalForTransactions,
  sumAggregateRowConfig,
  useStatisticalHighlights
} from '../composables/useAggregatedGroups'
import { useRoute, RouterLink } from 'vue-router'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import PieChart from '../components/charts/PieChart.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchMonthCategories } from '../js/api'
import { useResultQuery } from '../composables/useResultQuery'
import type { AggregatedTransactionsResponse } from '../types/api'
import { formatMonthYear, createMonthDate } from '../js/dateUtils'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()
const statisticalStore = useStatisticalStore()

// Optional resultId filter, carried in the query string
const resultQuery = useResultQuery()

// Table columns (computed so translated titles follow locale changes
// without remounting the page)
const columns = computed<Column[]>(() => [
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
    formatValue: (value: unknown, row?: Record<string, unknown>) => String(((row as { total_display?: string })?.total_display) || value || '')
  }
])

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
    return fetchMonthCategories(params, {
      algorithms: statisticalStore.algorithms,
      direction: statisticalStore.direction
    })
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
})

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

// Table data: one row per category group of the month
const tableData = computed(() => {
  if (!monthCategoriesData.value) return []
  const groups = monthCategoriesData.value.groups || {}

  return buildGroupRows(groups, {
    keyColumn: 'category_id',
    labelFormatter: (categoryKey) => categoryKey
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

  return [sumAggregateRowConfig($gettext, 'category_id')]
})

// Cell highlights synced from the aggregation response
const { cellHighlightsByRowId } = useStatisticalHighlights(monthCategoriesData)

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
              :show-legend="true"
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
