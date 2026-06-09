<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
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

const { $gettext } = useGettext()
const route = useRoute()

// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

// Table columns
const columns: Column[] = [
  {
    key: 'category',
    title: $gettext('Category'),
    component: TableLink,
    componentProps: (value: string, row: Record<string, unknown>) => {
      const accountId = String(route.params.accountId || '')
      const monthId = String(route.params.monthId || '')
      const resultId = String(route.params.resultId || '')
      const categoryId = extractCategoryIdFromData(row)
      return {
        to: { name: 'category-month-transactions', params: { resultId, accountId, categoryId, monthId } },
        class: 'clickable',
        children: value
      }
    }
  },
  {
    key: 'total',
    title: $gettext('Total'),
    renderHtml: (value: unknown) => String((value as { display?: string })?.display || value || '')
  }
]

// Extract category_id from row data
function extractCategoryIdFromData(row: Record<string, unknown>): string {
  const category = row.category as string | undefined
  const categoryUrl = row.category_url as string | undefined
  if (categoryUrl) {
    const match = categoryUrl.match(/categories\/([^/]+)\/months/)
    if (match) return match[1]
  }
  return category || ''
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
  getPageTitle: (data) => `${$gettext('Details for Month')}: ${data.month_name}`,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: $gettext('Home'), to: '/' },
    { name: $gettext('Results'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: $gettext('Month Details'), active: true }
  ],
  navButtons: [
    {
      text: $gettext('Back to Results'),
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
    category: category.category,
    category_url: category.category_url,
    total: category.total,
    row_id: category.row_id,
    _rowIds: {
      total: category.row_id // Map total column to its row_id for cell-level highlighting
    }
  }))
})

// Cell highlights from API (keyed by row_id)
const cellHighlightsByRowId = computed(() => {
  return monthCategoriesData.value?.highlights || {}
})

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
    <div v-else-if="monthCategoriesData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ pageTitle }}</h1>
      </div>

      <!-- Account Card -->
      <CardComponent :title="monthCategoriesData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-6 mb-3">
            <VueDataTable
              id="datatable-month"
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

      <!-- Navigation -->
      <div v-if="navButtons && navButtons.length" class="row">
        <div class="col-md-6">
          <ButtonComponent
            v-for="(button, index) in navButtons"
            :key="index"
            :text="button.text"
            :variant="button.variant"
            :to="button.to"
            :size="button.size"
            class="mt-3 mb-3 me-2"
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No data found') }}
    </div>
  </div>
</template>
