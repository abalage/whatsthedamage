<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { fetchResults } from '../js/api'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import type { _ResultsApiResponse } from '../types/api'

const { $gettext } = useGettext()
const route = useRoute()


const resultId = computed(() => {
  const id = route.params.resultId
  return typeof id === 'string' ? id : null
})

const resultsData = ref<_ResultsApiResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const loadResults = async () => {
  if (!resultId.value) {
    error.value = 'No result ID provided'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null

    const response = await fetchResults(resultId.value)

    resultsData.value = response
    // Set highlights for statistical cell highlighting
    window.highlights = resultsData.value?.accounts_data.highlights || {}

    // Set isLoading to false BEFORE initializing DataTables so the results block renders
    isLoading.value = false

    // Wait for Vue to render the tables with the new data
    await nextTick()

    // Set translation strings for DataTables export buttons
    window.exportCsvText = $gettext('Export CSV')
    window.exportExcelText = $gettext('Export Excel')

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    isLoading.value = false
  }
}

// Flatten all transactions for the data table
const allTransactions = computed(() => {
  if (!resultsData.value) return []

  const transactions = []

  for (const account of resultsData.value.accounts_data.accounts) {
    for (const aggRow of account.dt_response.data) {
      for (const detail of aggRow.details) {
        transactions.push({
          date: detail.date.display,
          category: aggRow.category,
          merchant: detail.merchant,
          amount: detail.amount.display,
          currency: detail.currency,
          account: account.name,
          type: detail.type || '',
          confidence: detail.confidence !== null ? detail.confidence.toString() : '',
          notice: detail.notice || '',
          row_id: detail.row_id
        })
      }
    }
  }

  return transactions
})

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="container">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ $gettext('Results') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Details') }}</li>
      </ol>
    </nav>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </div>
      <p class="mt-2">{{ $gettext('Loading results') }}...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="resultsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ $gettext('Transaction Details') }}</h1>
        <div class="view-toggle">
          <!-- View toggle would go here -->
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-md-12">
          <div class="table-responsive">
            <table id="detail-datatable" class="table table-bordered" data-datatable="true">
              <thead>
                <tr>
                  <th>{{ $gettext('Date') }}</th>
                  <th>{{ $gettext('Category') }}</th>
                  <th>{{ $gettext('Merchant') }}</th>
                  <th>{{ $gettext('Amount') }}</th>
                  <th>{{ $gettext('Currency') }}</th>
                  <th>{{ $gettext('Account') }}</th>
                  <th>{{ $gettext('Type') }}</th>
                  <th>{{ $gettext('Confidence') }}</th>
                  <th>{{ $gettext('Notice') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="transaction in allTransactions" :key="transaction.row_id">
                  <td>{{ transaction.date }}</td>
                  <td>{{ transaction.category }}</td>
                  <td>{{ transaction.merchant }}</td>
                  <td>{{ transaction.amount }}</td>
                  <td>{{ transaction.currency }}</td>
                  <td>{{ transaction.account }}</td>
                  <td>{{ transaction.type }}</td>
                  <td>{{ transaction.confidence }}</td>
                  <td>{{ transaction.notice }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <div class="row">
        <div class="col-md-6">
          <ButtonComponent
            :text="$gettext('Back to Results')"
            variant="secondary"
            :to="{ name: 'results', query: { resultId: resultId } }"
            class="mt-3 mb-3"
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No results found') }}
    </div>
  </div>
</template>

<style scoped>
/* Component-specific styles can be added here */
</style>