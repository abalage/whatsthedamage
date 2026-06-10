<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useStatisticalStore } from '../stores/statistical.js'
import {
  useDrilldownData,
  type BreadcrumbItem
} from '../composables/useDrilldownData.js'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import { fetchCategoryMonths } from '../js/api.js'
import type { CategoryMonthsApiResponse } from '../types/api.js'

const { $gettext } = useGettext()

const route = useRoute()
const statisticalStore = useStatisticalStore()

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
    componentProps: (value: unknown, row: Record<string, unknown>) => {
      const resultId = String(row.resultId || '')
      const accountId = String(row.accountId || '')
      const categoryId = String(row.categoryId || '')
      const monthId = extractMonthIdFromData(row)
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
    renderHtml: (value: unknown, row: Record<string, unknown>) => String((row as { total_display?: string }).total_display || value || '')
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
  breadcrumbItems,
  navButtons
} = useDrilldownData<CategoryMonthsApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.categoryId) {
      throw new Error('Missing required parameters for category months fetch')
    }
    return fetchCategoryMonths(params)
  },
  getPageTitle: (data) => `${$gettext('Details')}: ${data.category_name}`,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Results'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: $gettext('Category Details'), active: true }
  ],
  navButtons: [
    {
      text: $gettext('Back to Categories'),
      to: { name: 'results', query: { resultId: getRouteParam('resultId') } },
      variant: 'secondary'
    }
  ],
  errorMessageKey: 'categoryMonthsLoadError'
})



// Table data
const tableData = computed(() => {
  if (!categoryMonthsData.value) return []
  return categoryMonthsData.value.data.map(month => ({
    month: month.month,
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
    <div v-else-if="categoryMonthsData">
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
            class="mt-3 mb-3"
          />
        </div>
      </div>

      <!-- Account Card -->
      <CardComponent :title="categoryMonthsData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-6 mb-3">
            <VueDataTable
              id="datatable-category"
              :data="tableData"
              :columns="columns"
              :cell-highlights-by-row-id="cellHighlightsByRowId"
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
      {{ $gettext('No data found') }}
    </div>
  </div>
</template>
