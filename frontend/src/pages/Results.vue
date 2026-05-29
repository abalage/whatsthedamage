<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { fetchResults as fetchResultsApi } from '../js/api'
import { useFeedbackStore } from '../stores/feedback'
import { useGettext } from 'vue3-gettext'
import type { _ResultsApiResponse } from '../types/api'

const { $gettext } = useGettext()

// Local type for the account data structure used in this component
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
        date: { display: string }
        amount: { display: string }
        merchant: string
      }>
      row_id: string
    }>
  }
}

const feedback = useFeedbackStore()
const route = useRoute()


// Try both camelCase and snake_case for the query parameter
const resultId = computed(() => {
  const id = route.query.resultId ?? route.query.result_id
  return typeof id === 'string' ? id : null
})
const resultsData = ref<_ResultsApiResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const DEFERRED_TIMEOUT = 0

const loadResults = async () => {
  if (!resultId.value) {
    error.value = 'No result ID provided'
    isLoading.value = false

    // Fallback: Try to fetch some demo data or show a helpful message
    // For development/testing, we could fetch a hardcoded result
    // In production, this would redirect to the upload form
    try {
      const fallbackResponse = await fetchResultsApi('demo-result-id')
      resultsData.value = fallbackResponse

      // Initialize DataTables for fallback data
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, DEFERRED_TIMEOUT))
      window.exportCsvText = $gettext('Export CSV')
      window.exportExcelText = $gettext('Export Excel')

      // Set highlights for statistical cell highlighting
      window.highlights = fallbackResponse.accounts_data?.highlights || {}

      window.initMainPage()
    } catch (fallbackError) {
      const message = fallbackError instanceof Error ? fallbackError.message : String(fallbackError)
      feedback.showError(`Failed to load fallback data: ${message}`)
    }

    return
  }

  try {
    // Fetch results data from the API endpoint we created
    const response = await fetchResultsApi(resultId.value)
    resultsData.value = response
    error.value = null

    // Set isLoading to false BEFORE initializing DataTables so the results block renders
    isLoading.value = false

    // Wait for Vue to render the tables with the new data
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, DEFERRED_TIMEOUT))

    // Set translation strings for DataTables export buttons
    window.exportCsvText = $gettext('Export CSV')
    window.exportExcelText = $gettext('Export Excel')

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
  const monthMap = new Map<number, [string, number]>()
  for (const row of account.dt_response.data) {
    const monthField = row.date
    monthMap.set(monthField.timestamp, [monthField.display, monthField.timestamp])
  }
  return Array.from(monthMap.values()).sort((a, b) => b[1] - a[1]) // eslint-disable-line no-magic-numbers
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
    .join('\n')
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
  loadResults()
})
</script>

<template>
  <div class="container">
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Results') }}</li>
      </ol>
    </nav>

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </div>
      <p class="mt-2">{{ $gettext('Loading results') }}...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-else-if="resultsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ $gettext('Processed results') }}</h1>
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
                    <th>{{ $gettext('Categories') }}</th>
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
                        data-bs-html="false"
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
          <router-link to="/" class="btn btn-secondary mt-3 mb-3">{{ $gettext('Back to Form') }}</router-link>
          <router-link :to="{ name: 'details', params: { resultId: resultId } }" class="btn btn-outline-secondary mt-3 mb-3 ms-2">{{ $gettext('View All Details') }}</router-link>
        </div>
      </div>
    </div>

    <div v-else class="alert alert-info">
      <p>{{ $gettext('No results found') }}</p>
      <p v-if="!resultId">
        {{ $gettext('No result ID was provided.') }}
        <router-link to="/" class="alert-link">{{ $gettext('Please upload a CSV file first.') }}</router-link>
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