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

interface TransactionData {
  date: {
    display: string
  }
  amount: {
    display: string
  }
  merchant: string
  row_id: string
}

interface CategoryMonthTransactionsResponse {
  result_id: string
  account_id: string
  account_name: string
  category_id: string
  category_name: string
  month_id: string
  month_name: string
  data: TransactionData[]
  highlights?: Record<string, string[]>
}

const resultId = computed(() => route.params.resultId as string)
const accountId = computed(() => route.params.accountId as string)
const categoryId = computed(() => route.params.categoryId as string)
const monthId = computed(() => route.params.monthId as string)

const transactionsData = ref<CategoryMonthTransactionsResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const fetchTransactions = async () => {
  if (!resultId.value || !accountId.value || !categoryId.value || !monthId.value) {
    error.value = 'Missing required parameters'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null

    const response = await fetchWithErrorHandling<CategoryMonthTransactionsResponse>(
      `${API_BASE_URL}/results/${resultId.value}/accounts/${accountId.value}/categories/${categoryId.value}/months/${monthId.value}/transactions`
    )

    transactionsData.value = response
    error.value = null

    // Set isLoading to false BEFORE initializing DataTables so the results block renders
    isLoading.value = false

    // Wait for Vue to render the tables with the new data
    await nextTick()

    // Set translation strings for DataTables export buttons
    window.exportCsvText = t('Export CSV')
    window.exportExcelText = t('Export Excel')

    // Set highlights for statistical cell highlighting
    window.highlights = transactionsData.value?.highlights || {}

    // Initialize DataTables now that tables exist in DOM
    window.initMainPage()
  } catch (err) {
    console.error('Failed to fetch transactions:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load transactions'
    isLoading.value = false
  }
}



onMounted(() => {
  fetchTransactions()
})
</script>

<template>
  <div class="container">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ t('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ t('Results') }}</router-link></li>
        <li class="breadcrumb-item">
          <router-link
            :to="{ name: 'category-months', params: { resultId: resultId, accountId: accountId, categoryId: categoryId } }"
          >
            {{ t('Category Months') }}
          </router-link>
        </li>
        <li class="breadcrumb-item active" aria-current="page">{{ t('Transaction Details') }}</li>
      </ol>
    </nav>

    <StatisticalControls v-if="transactionsData" :resultId="resultId" />

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
    <div v-else-if="transactionsData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ t('Transaction Details') }}: {{ transactionsData.category_name }} - {{ transactionsData.month_name }}</h1>
      </div>

      <!-- Account Card -->
      <CardComponent :title="transactionsData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-8 mb-3">
            <div class="table-responsive">
              <table id="transaction-details-table" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Date') }}</th>
                    <th>{{ t('Amount') }}</th>
                    <th>{{ t('Merchant') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="transaction in transactionsData.data" :key="transaction.row_id">
                    <td>{{ transaction.date.display }}</td>
                    <td :data-row-id="transaction.row_id" class="">
                      {{ transaction.amount.display }}
                    </td>
                    <td>{{ transaction.merchant }}</td>
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
          <router-link :to="{ name: 'category-months', params: { resultId: resultId, accountId: accountId, categoryId: categoryId } }" class="btn btn-secondary me-2 mt-3 mb-3">{{ t('Back to Category Months') }}</router-link>
          <router-link :to="{ name: 'results', query: { resultId: resultId } }" class="btn btn-outline-secondary mt-3 mb-3">{{ t('Back to Results') }}</router-link>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ t('noTransactionsFound') }}
    </div>
  </div>
</template>

<style scoped>
/* Component-specific styles can be added here */
</style>