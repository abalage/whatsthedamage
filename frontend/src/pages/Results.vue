<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { fetchWithErrorHandling } from '../js/api'
import { useFeedbackStore } from '../stores/feedback'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const localeStore = useLocaleStore()
const feedback = useFeedbackStore()
const route = useRoute()
const router = useRouter()

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
  month_urls: Record<string, { month_url: string }>
  category_urls: Record<string, { category_url: string }>
  cell_urls: Record<string, { cell_url: string }>
}

interface ResultsResponse {
  result_id: string
  accounts_data: {
    accounts: AccountData[]
    highlights: any
  }
  drilldown_urls_by_account: Record<string, DrilldownUrls>
}

// Try both camelCase and snake_case for the query parameter
const resultId = computed(() => route.query.resultId as string || route.query.result_id as string)
const resultsData = ref<ResultsResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const fetchResults = async () => {
  // Debug: Log the route query parameters
  console.log('Route query parameters:', route.query)
  console.log('Result ID from query (resultId):', route.query.resultId)
  console.log('Result ID from query (result_id):', route.query.result_id)
  console.log('Final result ID:', resultId.value)
  
  if (!resultId.value) {
    error.value = 'No result ID provided'
    console.error('No result ID found in query parameters')
    isLoading.value = false
    
    // Fallback: Try to fetch some demo data or show a helpful message
    console.log('Attempting fallback data fetch...')
    
    // For development/testing, we could fetch a hardcoded result
    // In production, this would redirect to the upload form
    try {
      const fallbackResponse = await fetchWithErrorHandling<ResultsResponse>(`${API_BASE_URL}/results/demo-result-id`)
      resultsData.value = fallbackResponse
      console.log('Fallback data loaded successfully')
    } catch (fallbackError) {
      console.error('Fallback fetch also failed:', fallbackError)
      // Don't set error here since we already have the original error
    }
    
    return
  }

  try {
    // Fetch results data from the API endpoint we created
    const response = await fetchWithErrorHandling<ResultsResponse>(`${API_BASE_URL}/results/${resultId.value}`)
    resultsData.value = response
  } catch (err) {
    console.error('Failed to fetch results:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    feedback.showError('Failed to load results: ' + error.value)
  } finally {
    isLoading.value = false
  }
}

const getMonthsForAccount = (account: AccountData) => {
  const months = new Set<[string, number]>()
  for (const row of account.dt_response.data) {
    const monthField = row.date
    months.add([monthField.display, monthField.timestamp])
  }
  return Array.from(months).sort((a, b) => b[1] - a[1])
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

const getDetailsString = (details: any[]) => {
  return details
    .map(detail => `${detail.date.display}: ${detail.amount.display} - ${detail.merchant}`)
    .join('<br>')
}

const navigateToCategoryMonths = (accountId: string, category: string) => {
  router.push({
    name: 'category-months',
    params: {
      resultId: resultId.value,
      accountId: accountId,
      categoryId: category
    }
  })
}

const navigateToMonthCategories = (accountId: string, monthTs: number) => {
  // Use timestamp directly as month_id (the backend expects the raw timestamp)
  router.push({
    name: 'month-categories',
    params: {
      resultId: resultId.value,
      accountId: accountId,
      monthId: String(monthTs)
    }
  })
}

const navigateToCategoryMonthTransactions = (accountId: string, category: string, monthTs: number) => {
  // Use timestamp directly as month_id (the backend expects the raw timestamp)
  router.push({
    name: 'category-month-transactions',
    params: {
      resultId: resultId.value,
      accountId: accountId,
      categoryId: category,
      monthId: String(monthTs)
    }
  })
}

onMounted(() => {
  console.log('Results component mounted')
  console.log('Current route:', route)
  console.log('Current route path:', route.path)
  console.log('Current route query:', route.query)
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
              <table class="table table-bordered" :id="`datatable-${account.id}`" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Categories') }}</th>
                    <th v-for="[monthDisplay, monthTs] in getMonthsForAccount(account)" 
                        :key="monthTs" 
                        :data-order="monthTs">
                      <a href="#" class="clickable" @click.prevent="navigateToMonthCategories(account.id, monthTs)">{{ monthDisplay }}</a>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="category in Object.keys(buildCategoryMonthMap(account)).sort()" :key="category">
                    <td>
                      <a href="#" class="clickable" @click.prevent="navigateToCategoryMonths(account.id, category)">{{ category }}</a>
                    </td>
                    <td v-for="[monthDisplay, monthTs] in getMonthsForAccount(account)" 
                        :key="monthTs" 
                        :data-order="buildCategoryMonthMap(account)[category][monthTs]?.total.raw || 0">
                      <template v-if="buildCategoryMonthMap(account)[category][monthTs]">
                        <div v-if="buildCategoryMonthMap(account)[category][monthTs].details" 
                             tabindex="0" 
                             data-bs-toggle="popover" 
                             data-bs-trigger="hover focus" 
                             data-bs-html="true" 
                             :data-bs-content="getDetailsString(buildCategoryMonthMap(account)[category][monthTs].details)" 
                             data-bs-placement="top" 
                             data-bs-custom-class="popover-wide">
                          <a href="#" class="clickable" @click.prevent="navigateToCategoryMonthTransactions(account.id, category, monthTs)">
                            {{ buildCategoryMonthMap(account)[category][monthTs].total.display }}
                          </a>
                        </div>
                        <div v-else>
                          <a href="#" class="clickable" @click.prevent="navigateToCategoryMonthTransactions(account.id, category, monthTs)">
                            {{ buildCategoryMonthMap(account)[category][monthTs].total.display }}
                          </a>
                        </div>
                      </template>
                      <template v-else>
                        <div data-order="0"></div>
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
          <router-link :to="`/results/${resultId}/details`" class="btn btn-outline-secondary mt-3 mb-3 ms-2">{{ t('View All Details') }}</router-link>
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