<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { fetchWithErrorHandling } from '../js/api'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import StatisticalControls from '../components/ui/StatisticalControls.vue'


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v2'

const localeStore = useLocaleStore()
const route = useRoute()

const t = (key: string) => getTranslation(key, localeStore.locale)

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

interface MonthData {
  month: string
  month_timestamp: number
  total: {
    display: string
    raw: number
  }
  row_id: string
  cell_url: string
}

interface CategoryMonthsResponse {
  result_id: string
  account_id: string
  account_name: string
  category_id: string
  category_name: string
  data: MonthData[]
  drilldown_urls?: Record<string, DrilldownUrls>
  highlights?: Record<string, string[]>
}

const resultId = computed(() => route.params.resultId as string)
const accountId = computed(() => route.params.accountId as string)
const categoryId = computed(() => route.params.categoryId as string)

const categoryMonthsData = ref<CategoryMonthsResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const fetchCategoryMonths = async () => {
  if (!resultId.value || !accountId.value || !categoryId.value) {
    error.value = 'Missing required parameters'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null

    const response = await fetchWithErrorHandling<CategoryMonthsResponse>(
      `${API_BASE_URL}/results/${resultId.value}/accounts/${accountId.value}/categories/${categoryId.value}/months`
    )

    categoryMonthsData.value = response
    error.value = null

    // Set isLoading to false BEFORE initializing DataTables so the results block renders
    isLoading.value = false

    // Wait for Vue to render the tables with the new data
    await nextTick()

    // Set translation strings for DataTables export buttons
    window.exportCsvText = t('Export CSV')
    window.exportExcelText = t('Export Excel')

    // Set highlights for statistical cell highlighting
    window.highlights = categoryMonthsData.value?.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load category months'
    isLoading.value = false
  }
}

/**
 * Extract month_id from month data (from cell_url or month_timestamp)
 */
const extractMonthId = (month: MonthData): string => {
  // Try to extract from cell_url first
  const MONTH_ID_CAPTURE_GROUP = 1
  if (month.cell_url) {
    const match = month.cell_url.match(/months\/([^/]+)\/transactions/)
    if (match) {
      return match[MONTH_ID_CAPTURE_GROUP]
    }
  }
  // Fallback to month_timestamp as string
  return String(month.month_timestamp)
}



onMounted(() => {
  fetchCategoryMonths()
})
</script>

<template>
  <div class="container">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ t('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ t('Results') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ t('Category Details') }}</li>
      </ol>
    </nav>

    <StatisticalControls v-if="categoryMonthsData" :result-id="resultId" />

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
    <div v-else-if="categoryMonthsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ t('Details for Category') }}: {{ categoryMonthsData.category_name }}</h1>
      </div>

      <!-- Account Card -->
      <CardComponent :title="categoryMonthsData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-6 mb-3">
            <div class="table-responsive">
              <table id="datatable-category" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Month') }}</th>
                    <th>{{ t('Total') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="month in categoryMonthsData.data" :key="month.row_id">
                    <td>
                      <router-link :to="{ name: 'category-month-transactions', params: { resultId: resultId, accountId: accountId, categoryId: categoryId, monthId: extractMonthId(month) } }" class="clickable">{{ month.month }}</router-link>
                    </td>
                    <td :data-row-id="month.row_id" class="">
                      {{ month.total.display }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </CardComponent>

      <!-- Navigation -->
      <div class="row">
        <div class="col-md-6">
          <ButtonComponent
            :text="t('Back to Results')"
            variant="secondary"
            :to="{ name: 'results', query: { resultId: resultId } }"
            class="mt-3 mb-3"
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