<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { fetchProcessingResultMetadata, fetchTransactionsByResult } from '../js/api.js'
import { buildResultQuery } from '../js/routeUtils.js'
import { useCategoriesStore } from '../stores/categories.js'
import { RouterLink } from 'vue-router'
import { formatDateISO } from '../js/dateUtils.js'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import type { ProcessingResultMetadata, TransactionListItem } from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()

const resultId = computed(() => {
  const id = route.query.resultId ?? route.query.result_id
  return typeof id === 'string' && id !== '' ? id : null
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

const metadata = ref<ProcessingResultMetadata | null>(null)
const transactions = ref<TransactionListItem[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

const loadResults = async () => {
  try {
    isLoading.value = true
    error.value = null

    // Fetch metadata only when scoped to a specific result
    metadata.value = resultId.value
      ? await fetchProcessingResultMetadata(resultId.value)
      : null

    // Fetch transactions, optionally filtered by result
    const response = await fetchTransactionsByResult(resultId.value ?? undefined, { limit: 10000 })
    transactions.value = response.transactions

    isLoading.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    isLoading.value = false
  }
}

// Helper function to format transaction date from ISO string or timestamp
// Uses the new utility function that handles both ISO strings and epoch timestamps
function formatDateForDisplay(dateValue: string | undefined): string {
  return formatDateISO(dateValue)
}

// Flatten all transactions for the data table
const allTransactions = computed(() => {
  return transactions.value.map(txn => ({
    date: formatDateForDisplay(txn.date),
    category_id: txn.category_id || 'uncategorized',
    merchant: txn.original_partner || txn.partner || '',
    amount: txn.amount?.toFixed(2) || '',
    currency: txn.currency || '',
    account: txn.account,
    type: txn.transaction_type || '',
    confidence: txn.confidence?.toString() ?? '',
    notice: txn.notice || '',
    row_id: String(txn.id)
  }))
})

onMounted(() => {
  loadResults()
})

// Reload when the resultId query filter changes while the page is reused
watch(resultId, () => {
  loadResults()
})
</script>

<template>
  <div class="container-fluid">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: buildResultQuery(resultId) }">{{ $gettext('Categories') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Transactions') }}</li>
      </ol>
    </nav>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-on-primary">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </output>
      <p class="mt-2">{{ $gettext('Loading results') }}...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-status-danger text-on-light alert">
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="metadata || transactions.length > 0">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">
          {{ $gettext('Transactions') }}
          <span v-if="!resultId" class="text-secondary fs-5">({{ $gettext('All Transactions') }})</span>
        </h1>
        <div class="d-flex gap-2">
          <RouterLink
            :to="{ name: 'results', query: buildResultQuery(resultId) }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Back to Categories') }}
          </RouterLink>
        </div>
      </div>

      <div class="card mb-4" style="width: fit-content; margin: 0 auto">
        <div class="card-header">
          {{ $gettext('Transactions') }}
        </div>
        <div class="card-body">
          <VueDataTable
            id="detail-datatable"
            :data="allTransactions"
            :columns="columns"
            wrapper-class="w-auto"
            show-column-filters
            show-pagination
            :page-size="100"
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
