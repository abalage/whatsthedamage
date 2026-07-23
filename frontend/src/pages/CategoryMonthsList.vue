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
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchCategoryMonths } from '../js/api.js'
import type { CategoryMonthsApiResponse } from '../types/api.js'
import { formatMonthYear } from '../js/dateUtils.js'

const { $gettext } = useGettext()

const route = useRoute()
const statisticalStore = useStatisticalStore()
const categoriesStore = useCategoriesStore()

// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

// Table columns
const columns: Column[] = [
  {
    key: 'month',
    title: $gettext('Month'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const resultId = String(row?.resultId || '')
      const accountId = String(row?.accountId || '')
      const categoryId = String(row?.categoryId || '')
      const monthId = extractMonthIdFromData(row ?? {})
      return {
        to: { name: 'category-month-transactions', params: { resultId, accountId, categoryId, monthId } },
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
  const cellUrl = row.cell_url as string | undefined
  const monthTimestamp = row.month_timestamp as number | string | undefined
  if (cellUrl) {
    const match = cellUrl.match(/months\/([^/]+)\/transactions/)
    if (match) return match[1]
  }
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
} = useDrilldownData<CategoryMonthsApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.categoryId) {
      throw new Error('Missing required parameters for category months fetch')
    }
    return fetchCategoryMonths(params)
  },
  titleBaseKey: 'Category Details',
  titleFormat: 'category',
  titleExtractor: (data: CategoryMonthsApiResponse) => ({
    categoryId: data.category_id
  }),
  breadcrumbItems: (data: CategoryMonthsApiResponse | null): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Categories'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: data ? categoriesStore.getCategoryDisplayName(data.category_id) : $gettext('Category Details'), active: true }
  ],
  errorMessageKey: 'categoryMonthsLoadError'
})

// Table data
const tableData = computed(() => {
  if (!categoryMonthsData.value) return []
  return categoryMonthsData.value.data.map(month => ({
    month: formatMonthYear(month.month_timestamp),
    total: month.total.raw,
    total_display: month.total.display,
    row_id: month.row_id,
    cell_url: month.cell_url,
    month_timestamp: month.month_timestamp,
    resultId,
    accountId,
    categoryId,
    _rowIds: {
      total: month.row_id // Map total column to its row_id for cell-level highlighting
    }
  }))
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!categoryMonthsData.value || categoryMonthsData.value.data.length === 0) return []

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
    <div v-else-if="categoryMonthsData">
      <PageHeader :title="pageTitle">
        <template #actions>
          <RouterLink
            :to="{ name: 'results', query: { resultId: getRouteParam('resultId') } }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Back to Categories') }}
          </RouterLink>
        </template>
      </PageHeader>

      <!-- Account Card -->
      <div class="card mb-4" style="width: fit-content; margin: 0 auto">
        <div class="card-header">
          {{ $gettext('Account') }}: {{ categoryMonthsData.account_formatted_id }}
          <span v-if="categoryMonthsData.account_currency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
            {{ categoryMonthsData.account_currency }}
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
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No data available') }}
    </div>
  </div>
</template>
