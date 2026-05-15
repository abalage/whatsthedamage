<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import {
  useDrilldownData,
  drilldownEndpoints,
  extractIdFromUrl,
  type BreadcrumbItem
} from '../composables/useDrilldownData'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import StatisticalControls from '../components/ui/StatisticalControls.vue'

interface DrilldownUrlInfo {
  category_url: string
  category_id: string
}

interface DrilldownUrls {
  account_id: string | null
  category_urls: Record<string, DrilldownUrlInfo>
  month_urls: Record<string, { month_url: string; month_id: string }>
  cell_urls: Record<string, { cell_url: string; category_id: string; month_id: string }>
}

interface CategoryData {
  category: string
  total: {
    display: string
    raw: number
  }
  row_id: string
  category_url: string
}

interface MonthCategoriesResponse {
  result_id: string
  account_id: string
  account_name: string
  month_id: string
  month_name: string
  data: CategoryData[]
  drilldown_urls?: Record<string, DrilldownUrls>
  highlights?: Record<string, string[]>
}

const localeStore = useLocaleStore()
const route = useRoute()

const t = (key: string) => getTranslation(key, localeStore.locale)

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
} = useDrilldownData<MonthCategoriesResponse>({
  buildEndpoint: drilldownEndpoints.monthCategories,
  getPageTitle: (data) => `${t('Details for Month')}: ${data.month_name}`,
  breadcrumbItems: (): BreadcrumbItem[] => [
    { name: t('Home'), to: '/' },
    { name: t('Results'), to: { name: 'results', query: { resultId: getRouteParam('resultId') } } },
    { name: t('Month Details'), active: true }
  ],
  navButtons: [
    {
      text: t('Back to Results'),
      to: { name: 'results', query: { resultId: getRouteParam('resultId') } },
      variant: 'secondary'
    }
  ],
  onDataLoaded: (data) => {
    // Set translation strings for DataTables export buttons
    window.exportCsvText = t('Export CSV')
    window.exportExcelText = t('Export Excel')

    // Set highlights for statistical cell highlighting
    window.highlights = data.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
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

    <StatisticalControls v-if="monthCategoriesData" :result-id="resultId" />

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ t('loading') }}...</span>
      </div>
      <p class="mt-2">{{ t('loadingData') }}...</p>
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
                    <th>{{ t('Category') }}</th>
                    <th>{{ t('Total') }}</th>
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
      {{ t('noDataFound') }}
    </div>
  </div>
</template>

<style scoped>
.clickable {
  cursor: pointer;
  text-decoration: underline;
}

.clickable:hover {
  color: #0d6efd;
}
</style>
