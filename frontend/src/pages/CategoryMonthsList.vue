<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical'
import { useCategoriesStore } from '../stores/categories'
import { useDrilldownData } from '../composables/useDrilldownData'
import {
  buildGroupRows,
  sumAggregateRowConfig,
  averageAggregateRowConfig,
  useStatisticalHighlights
} from '../composables/useAggregatedGroups'
import { RouterLink } from 'vue-router'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchAggregatedTransactions } from '../js/api'
import { buildResultQuery } from '../js/routeUtils'
import { useResultQuery } from '../composables/useResultQuery'
import type { AggregatedTransactionsResponse } from '../types/api'
import { formatMonthKey, extractMonthKey, createMonthDate } from '../js/dateUtils'
import BarChart from '../components/charts/BarChart.vue'

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
      group_by: 'month',
      algorithms: statisticalStore.algorithms,
      direction: statisticalStore.direction
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

// Table data: one row per month group of the category
const tableData = computed(() => {
  if (!categoryMonthsData.value) return []

  const groups = categoryMonthsData.value.groups || {}

  return buildGroupRows(groups, {
    keyColumn: 'month',
    labelFormatter: formatMonthKey,
    rowIdOf: extractMonthKey,
    extraFields: (monthKey) => {
      const monthDate = createMonthDate(extractMonthKey(monthKey))
      return {
        month_timestamp: monthDate ? monthDate.getTime() / 1000 : 0,
        resultId: resultId.value,
        accountId: accountId.value,
        categoryId: categoryId.value
      }
    }
  })
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!categoryMonthsData.value || !categoryMonthsData.value.groups || Object.keys(categoryMonthsData.value.groups).length === 0) return []

  return [
    sumAggregateRowConfig($gettext, 'month'),
    averageAggregateRowConfig($gettext, 'month')
  ]
})

// Cell highlights synced from the aggregation response
const { cellHighlightsByRowId } = useStatisticalHighlights(categoryMonthsData)

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
