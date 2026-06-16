<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { fetchResults } from '../js/api.js'
import { useCategoriesStore } from '../stores/categories.js'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import CardComponent from '../components/ui/CardComponent.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import type { ResultsApiResponse } from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()

const resultId = computed(() => {
  const id = route.params.resultId
  return typeof id === 'string' ? id : null
})

// Table columns definition
const columns: Column[] = [
  { key: 'date', title: $gettext('Date') },
  {
    key: 'category_id',
    title: $gettext('Category'),
    component: TableLink,
    componentProps: (value: unknown, row?: Record<string, unknown>) => {
      const categoryId = categoriesStore.extractCategoryIdFromData(row ?? {})
      const categoryDisplayName = categoriesStore.getCategoryDisplayName(categoryId)
      return {
        to: '#',
        class: 'clickable',
        children: categoryDisplayName
      }
    }
  },
  { key: 'merchant', title: $gettext('Merchant') },
  { key: 'amount', title: $gettext('Amount') },
  { key: 'currency', title: $gettext('Currency') },
  { key: 'account', title: $gettext('Account') },
  { key: 'type', title: $gettext('Type') },
  { key: 'confidence', title: $gettext('Confidence') },
  { key: 'notice', title: $gettext('Notice') },
]

const resultsData = ref<ResultsApiResponse | null>(null)
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

    isLoading.value = false
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
          category_id: aggRow.category_id,
          merchant: detail.merchant,
          amount: detail.amount.display,
          currency: detail.currency,
          account: account.name,
          type: detail.type || '',
          confidence: detail.confidence?.toString() ?? '',
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
  <div class="container-fluid">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ $gettext('Categories') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Transactions') }}</li>
      </ol>
    </nav>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-primary">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </output>
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
        <div class="d-flex gap-2">
          <ButtonComponent
            :text="$gettext('Back to Categories')"
            variant="secondary"
            :to="{ name: 'results', query: { resultId: resultId } }"
            class="mt-3 mb-3"
          />
        </div>
      </div>

      <CardComponent :title="$gettext('Transactions')" class="mb-4" width="fit-content">
          <VueDataTable
            id="detail-datatable"
            :data="allTransactions"
            :columns="columns"
            wrapper-class="w-auto"
            show-column-filters
          />
      </CardComponent>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ $gettext('No results found') }}
    </div>
  </div>
</template>
