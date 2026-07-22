<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical.js'
import { useCategoriesStore } from '../stores/categories.js'
import {
  useDrilldownData,
  type BreadcrumbItem
} from '../composables/useDrilldownData.js'
import { RouterLink } from 'vue-router'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchMonthCategories } from '../js/api.js'
import type { MonthCategoriesApiResponse } from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()
const statisticalStore = useStatisticalStore()

// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

// Import formatMonthYear for breadcrumb
import { formatMonthYear } from '../js/dateUtils.js'

// Table columns
const columns: Column[] = [
  {
    key: 'category_id',
    title: $gettext('Category'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const accountId = String(route.params.accountId || '')
      const monthId = String(route.params.monthId || '')
      const resultId = String(route.params.resultId || '')
      const categoryId = extractCategoryIdFromData(row ?? {})
      const categoryDisplayName = categoriesStore.getCategoryDisplayName(String(row?.category_id ?? ''))
      return {
        to: { name: 'category-month-transactions', params: { resultId, accountId, categoryId, monthId } },
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
  pageTitle,
  breadcrumbItems
} = useDrilldownData<MonthCategoriesApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.monthId) {
      throw new Error('Missing required parameters for month categories fetch')
    }
    return fetchMonthCategories(params)
  },
  titleBaseKey: 'Month Details',
  titleFormat: 'month',
  titleExtractor: (data: MonthCategoriesApiResponse) => ({
    monthTimestamp: data.month_timestamp
  }),
  breadcrumbItems: (data: MonthCategoriesApiResponse | null): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Categories'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: data ? formatMonthYear(data.month_timestamp) : $gettext('Month Details'), active: true }
  ],
  errorMessageKey: 'monthCategoriesLoadError'
})



// Table data with _rowIds mapping
const tableData = computed(() => {
  if (!monthCategoriesData.value) return []
  return monthCategoriesData.value.data.map(category => ({
    category_id: category.category_id,
    category_url: category.category_url,
    total: category.total.raw,
    total_display: category.total.display,
    row_id: category.row_id,
    _rowIds: {
      total: category.row_id // Map total column to its row_id for cell-level highlighting
    }
  }))
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!monthCategoriesData.value || monthCategoriesData.value.data.length === 0) return []

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
watch(() => monthCategoriesData.value, (newData) => {
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
    <div v-else-if="monthCategoriesData">
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
          {{ $gettext('Account') }}: {{ monthCategoriesData.account_formatted_id }}
          <span v-if="monthCategoriesData.account_currency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
            {{ monthCategoriesData.account_currency }}
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
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No data available') }}
    </div>
  </div>
</template>
