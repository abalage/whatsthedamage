<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { fetchWithErrorHandling } from '../js/api'
import { useFeedbackStore } from '../stores/feedback'
import StatisticalControls from '../components/ui/StatisticalControls.vue'


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v2'

const localeStore = useLocaleStore()
const feedback = useFeedbackStore()
const route = useRoute()

const t = (key: string) => getTranslation(key, localeStore.locale)

interface AccountData {
  id: string
  name: string
  dt_response: {
    data: Array<{
      category: string
      date: {
        display: string
        timestamp: number
      }
      total: {
        display: string
        raw: number
      }
      details: Array<{
        date: {
          display: string
        }
        amount: {
          display: string
        }
        merchant: string
      }>
      row_id: string
    }>
  }
}

interface DrilldownUrls {
  account_id: string | null
  category_urls: Record<string, { category_url: string; category_id: string }>
  month_urls: Record<string, { month_url: string; month_id: string }>
  cell_urls: Record<string, { cell_url: string; category_id: string; month_id: string }>
}

interface ResultsResponse {
  result_id: string
  accounts_data: {
    accounts: AccountData[]
    highlights: Record<string, string[]>
  }
  drilldown_urls_by_account: Record<string, DrilldownUrls>
}

// Try both camelCase and snake_case for the query parameter
const resultId = computed(() => route.query.resultId as string || route.query.result_id as string)
const resultsData = ref<ResultsResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const DEFERRED_TIMEOUT = 0

const fetchResults = async () => {
  if (!resultId.value) {
    error.value = 'No result ID provided'
    isLoading.value = false

    // Fallback: Try to fetch some demo data or show a helpful message
    // For development/testing, we could fetch a hardcoded result
    // In production, this would redirect to the upload form
    try {
      const fallbackResponse = await fetchWithErrorHandling<ResultsResponse>(`${API_BASE_URL}/results/demo-result-id`)
      resultsData.value = fallbackResponse

      // Initialize DataTables for fallback data
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, DEFERRED_TIMEOUT))
      window.exportCsvText = t('Export CSV')
      window.exportExcelText = t('Export Excel')

      // Set highlights for statistical cell highlighting
      window.highlights = fallbackResponse.accounts_data?.highlights || {}

      window.initMainPage()
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (fallbackError) {
      // Don't set error here since we already have the original error
    }

    return
  }

  try {
    // Fetch results data from the API endpoint we created
    const response = await fetchWithErrorHandling<ResultsResponse>(`${API_BASE_URL}/results/${resultId.value}`)
    resultsData.value = response
    error.value = null

    // Set isLoading to false BEFORE initializing DataTables so the results block renders
    isLoading.value = false

    // Wait for Vue to render the tables with the new data
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, DEFERRED_TIMEOUT))

    // Set translation strings for DataTables export buttons
    window.exportCsvText = t('Export CSV')
    window.exportExcelText = t('Export Excel')

    // Set highlights for statistical cell highlighting
    window.highlights = resultsData.value?.accounts_data.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    feedback.showError('Failed to load results: ' + error.value)
    isLoading.value = false
  }
}

const getMonthsForAccount = (account: AccountData) => {
  const TIMESTAMP_INDEX = 1
  const monthMap = new Map<number, [string, number]>()
  for (const row of account.dt_response.data) {
    const monthField = row.date
    monthMap.set(monthField.timestamp, [monthField.display, monthField.timestamp])
  }
  return Array.from(monthMap.values()).sort((a, b) => b[TIMESTAMP_INDEX] - a[TIMESTAMP_INDEX])
}

const buildCategoryMonthMap = (account: AccountData) => {
  const catMonthMap: Record<string, Record<number, any>> = {}

  for (const row of account.dt_response.data) {
    if (!catMonthMap[row.category]) {
      catMonthMap[row.category] = {}
    }
    const monthKey = row.date.timestamp
    catMonthMap[row.category][monthKey] = row
  }

  return catMonthMap
}

const getDetailsString = (details: Array<{ date: { display: string }, amount: { display: string }, merchant: string }>): string => {
  return details
    .map(detail => `${detail.date.display}: ${detail.amount.display} - ${detail.merchant}`)
    .join('<br>')
}

/**
 * Get category ID from drilldown URLs for a specific account and category
 */
const getCategoryId = (accountId: string, category: string): string => {
  const urls = resultsData.value?.drilldown_urls_by_account[accountId]
  return urls?.category_urls?.[category]?.category_id || category
}

/**
 * Get month ID from drilldown URLs for a specific account and month timestamp
 */
const getMonthId = (accountId: string, monthTs: number): string => {
  const urls = resultsData.value?.drilldown_urls_by_account[accountId]
  return urls?.month_urls?.[String(monthTs)]?.month_id || String(monthTs)
}



onMounted(() => {
  fetchResults()
})
</script>

<template>
  <div class="container">
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ t('Home') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ t('Results') }}</li>
      </ol>
    </nav>

    <StatisticalControls v-if="resultsData" :result-id="resultId" />

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ t('loading') }}...</span>
      </div>
      <p class="mt-2">{{ t('loadingResults') }}...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-else-if="resultsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ t('Processed results') }}</h1>
        <div class="view-toggle">
          <!-- View toggle would go here -->
        </div>
      </div>

      <div v-for="account in resultsData.accounts_data.accounts" :key="account.id" class="mb-5">
        <div class="card">
          <div class="card-header">
            <h3>{{ account.name }}</h3>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table :id="`datatable-${account.id}`" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Categories') }}</th>
                    <th
v-for="[monthDisplay, monthTs] in getMonthsForAccount(account)"
                        :key="monthTs"
                        :data-order="monthTs">
                      <router-link :to="{ name: 'month-categories', params: { resultId: resultId, accountId: account.id, monthId: getMonthId(account.id, monthTs) } }" class="clickable">{{ monthDisplay }}</router-link>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="category in Object.keys(buildCategoryMonthMap(account)).sort()" :key="category">
                    <td>
                      <router-link :to="{ name: 'category-months', params: { resultId: resultId, accountId: account.id, categoryId: getCategoryId(account.id, category) } }" class="clickable">{{ category }}</router-link>
                    </td>
                    <!-- eslint-disable-next-line vue/first-attribute-linebreak,vue/no-unused-vars -->
                    <td v-for="[monthDisplay, monthTs] in getMonthsForAccount(account)" :key="monthTs"
                        :data-order="buildCategoryMonthMap(account)[category][monthTs]?.total.raw ?? 0"
                        :data-row-id="buildCategoryMonthMap(account)[category][monthTs]?.row_id ?? ''"
                        :tabindex="buildCategoryMonthMap(account)[category][monthTs]?.details ? 0 : undefined"
                        :data-bs-toggle="buildCategoryMonthMap(account)[category][monthTs]?.details ? 'popover' : undefined"
                        :data-bs-trigger="buildCategoryMonthMap(account)[category][monthTs]?.details ? 'hover focus' : undefined"
                        :data-bs-html="buildCategoryMonthMap(account)[category][monthTs]?.details ? 'true' : undefined"
                        :data-bs-content="buildCategoryMonthMap(account)[category][monthTs]?.details ? getDetailsString(buildCategoryMonthMap(account)[category][monthTs].details) : undefined"
                        data-bs-placement="top"
                        data-bs-custom-class="popover-wide">
                      <template v-if="buildCategoryMonthMap(account)[category][monthTs]">
                        <router-link :to="{ name: 'category-month-transactions', params: { resultId: resultId, accountId: account.id, categoryId: getCategoryId(account.id, category), monthId: getMonthId(account.id, monthTs) } }" class="clickable">{{ buildCategoryMonthMap(account)[category][monthTs].total.display }}</router-link>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-6">
          <router-link to="/" class="btn btn-secondary mt-3 mb-3">{{ t('Back to Form') }}</router-link>
          <router-link :to="{ name: 'details', params: { resultId: resultId } }" class="btn btn-outline-secondary mt-3 mb-3 ms-2">{{ t('View All Details') }}</router-link>
        </div>
      </div>
    </div>

    <div v-else class="alert alert-info">
      <p>{{ t('noResultsFound') }}</p>
      <p v-if="!resultId">
        {{ t('noResultIdMessage') }}
        <router-link to="/" class="alert-link">{{ t('uploadFilePrompt') }}</router-link>
      </p>
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

.popover-wide {
  max-width: 500px;
}
</style>