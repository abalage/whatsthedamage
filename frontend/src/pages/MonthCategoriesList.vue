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
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import { fetchMonthCategories } from '../js/api.js'
import type { MonthCategoriesApiResponse } from '../types/api.js'
import { formatMonthYear } from '../js/dateUtils.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
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
    key: 'category_id',
    title: $gettext('Category'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const accountId = String(route.params.accountId || '')
      const monthId = String(route.params.monthId || '')
      const resultId = String(route.params.resultId || '')
      const categoryId = extractCategoryIdFromData(row ?? {})
      const categoryDisplayName = categoriesStore.getCategoryDisplayName(categoryId)
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
  breadcrumbItems,
  navButtons
} = useDrilldownData<MonthCategoriesApiResponse>({
  fetchData: async (params) => {
    if (!params.resultId || !params.accountId || !params.monthId) {
      throw new Error('Missing required parameters for month categories fetch')
    }
    return fetchMonthCategories(params)
  },
  getPageTitle: (data) => `${$gettext('Details')}: ${formatMonthYear(data.month_timestamp)}`,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Categories'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: $gettext('Month Details'), active: true }
  ],
  navButtons: [
    {
      text: $gettext('Back to Categories'),
      to: { name: 'results', query: { resultId: getRouteParam('resultId') } },
      variant: 'secondary'
    }
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
    <div v-else-if="monthCategoriesData">
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
      <CardComponent :title="monthCategoriesData.account_name" class="mb-4" width="fit-content">
            <VueDataTable
              id="datatable-month"
              :data="tableData"
              :columns="columns"
              :cell-highlights-by-row-id="cellHighlightsByRowId"
              :csv-text="$gettext('Export CSV')"
              :excel-text="$gettext('Export Excel')"
              wrapper-class="w-auto"
              show-column-filters
            />
      </CardComponent>


    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No data found') }}
    </div>
  </div>
</template>
