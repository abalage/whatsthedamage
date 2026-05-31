<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import {
  useDrilldownData,
  extractIdFromUrl,
  type BreadcrumbItem
} from '../composables/useDrilldownData'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import { fetchMonthCategories } from '../js/api'
import type { _MonthCategoriesApiResponse, CategoryData } from '../types/api'

const { $gettext } = useGettext()
const route = useRoute()

// Helper to safely get route params
const getRouteParam = (param: string): string | null => {
  const value = route.params[param]
  return typeof value === 'string' ? value : null
}

const {
  data: monthCategoriesData,
  isLoading,
  error,
  fetchData,
  resultId,
  accountId,
  monthId,
  pageTitle,
  breadcrumbItems,
  navButtons
} = useDrilldownData<_MonthCategoriesApiResponse>({
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
  onDataLoaded: (data) => {
    // Set translation strings for DataTables export buttons
    const w7 = globalThis as unknown as Window
    w7.exportCsvText = $gettext('Export CSV')
    w7.exportExcelText = $gettext('Export Excel')

    // Set highlights for statistical cell highlighting
    w7.highlights = data.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    w7.initMainPage()
  },
  errorMessageKey: 'monthCategoriesLoadError'
})

/**
 * Extract category_id from category data (from category_url or category name)
 */
const extractCategoryId = (category: CategoryData): string => {
  // Try to extract from category_url first
  return extractIdFromUrl(
    category.category_url,
    /categories\/([^/]+)\/months/,
    category.category
  )
}

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
            <div class="table-responsive">
              <table id="datatable-month" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ $gettext('Category') }}</th>
                    <th>{{ $gettext('Total') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="category in monthCategoriesData.data" :key="category.row_id">
                    <td>
                      <router-link
                        :to="{
                          name: 'category-month-transactions',
                          params: {
                            resultId: resultId,
                            accountId: accountId,
                            categoryId: extractCategoryId(category),
                            monthId: monthId
                          }
                        }"
                        class="clickable"
                      >{{ category.category }}</router-link>
                    </td>
                    <td :data-row-id="category.row_id" class="">
                      {{ category.total.display }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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

<style scoped>
.clickable {
  cursor: pointer;
  text-decoration: underline;
}

.clickable:hover {
  color: var(--primary-color);
}
</style>
