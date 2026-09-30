<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { fetchAllTransactions, fetchProcessingResultMetadata, updateTransaction } from '../js/api.js'
import { buildResultQuery, extractResultId } from '../js/routeUtils.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useCategoriesStore } from '../stores/categories.js'
import { formatDateISO } from '../js/dateUtils.js'
import VueDataTable from '../components/data/VueDataTable.vue'
import EditableCategoryCell from '../components/data/EditableCategoryCell.vue'
import EditableTextCell from '../components/data/EditableTextCell.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import type {
  ProcessingResultMetadata,
  TransactionListItem,
  TransactionUpdatePayload
} from '../types/api.js'

const { $gettext } = useGettext()
const feedbackStore = useFeedbackStore()
const categoriesStore = useCategoriesStore()
const route = useRoute()

// Length limits matching the backend column sizes
const PARTNER_MAX_LENGTH = 255
const NOTICE_MAX_LENGTH = 500

// Optional resultId filter, carried in the query string
const resultId = computed(() => extractResultId(route.query as Record<string, unknown>))

// Persist a correction, refresh the local row, and confirm the outcome.
// Errors are rethrown so the editing cell can display them inline.
const saveCorrection = async (
  transactionId: number,
  payload: TransactionUpdatePayload
): Promise<void> => {
  const transaction = await updateTransaction(transactionId, payload)
  const index = transactions.value.findIndex(t => t.id === transaction.id)
  if (index !== -1) {
    transactions.value.splice(index, 1, transaction)
  }
  feedbackStore.showSuccess($gettext('Transaction updated'))
}

// Category id marker used by the frontend for uncategorized transactions
const UNCATEGORIZED = 'uncategorized'

// Dropdown options for the category filter: exactly the categories the
// backend reports as assignable, with stable ids as values and translated
// display names as labels, so filtering is language-agnostic
const categoryFilterOptions = computed(() => {
  return categoriesStore.categories
    .map(cat => ({
      value: cat.id,
      label: categoriesStore.getCategoryDisplayName(cat.id)
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

// Table columns definition
const columns = computed<Column[]>(() => [
  { key: 'date', title: $gettext('Date') },
  {
    key: 'category_id',
    title: $gettext('Category'),
    component: EditableCategoryCell,
    filterOptions: categoryFilterOptions.value,
    componentProps: (_value: unknown, row?: Record<string, unknown>) => ({
      categoryId: String(row?.category_id ?? UNCATEGORIZED),
      save: (categoryId: string | null) =>
        saveCorrection(Number(row?.transaction_id), { category_id: categoryId })
    })
  },
  {
    key: 'merchant',
    title: $gettext('Merchant'),
    component: EditableTextCell,
    componentProps: (value: unknown, row?: Record<string, unknown>) => ({
      value: String(value ?? ''),
      maxLength: PARTNER_MAX_LENGTH,
      allowEmpty: false,
      save: (partner: string) =>
        saveCorrection(Number(row?.transaction_id), { partner })
    })
  },
  { key: 'amount', title: $gettext('Amount') },
  { key: 'currency', title: $gettext('Currency') },
  { key: 'account', title: $gettext('Account') },
  { key: 'type', title: $gettext('Type') },
  { key: 'confidence', title: $gettext('Confidence') },
  {
    key: 'notice',
    title: $gettext('Notice'),
    component: EditableTextCell,
    componentProps: (value: unknown, row?: Record<string, unknown>) => ({
      value: String(value ?? ''),
      maxLength: NOTICE_MAX_LENGTH,
      allowEmpty: true,
      save: (notice: string) =>
        saveCorrection(Number(row?.transaction_id), { notice })
    })
  },
])

const metadata = ref<ProcessingResultMetadata | null>(null)
const transactions = ref<TransactionListItem[]>([])
const totalTransactionCount = ref(0)
const isLoading = ref(true)
const error = ref<string | null>(null)

// The unfiltered view fetches with a limit; warn when rows were left out
const isTruncated = computed(() => totalTransactionCount.value > transactions.value.length)

const loadResults = async () => {
  try {
    isLoading.value = true
    error.value = null

    // Fetch metadata only when scoped to a specific result
    metadata.value = resultId.value
      ? await fetchProcessingResultMetadata(resultId.value)
      : null

    // Fetch the complete dataset, optionally filtered by result
    const response = await fetchAllTransactions(resultId.value ?? undefined)
    transactions.value = response.transactions
    totalTransactionCount.value = response.total_count

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
    category_id: txn.category_id || UNCATEGORIZED,
    merchant: txn.partner || txn.original_partner || '',
    amount: txn.amount?.toFixed(2) || '',
    currency: txn.currency || '',
    account: txn.account,
    type: txn.transaction_type || '',
    confidence: txn.confidence?.toString() ?? '',
    notice: txn.notice || '',
    row_id: String(txn.id),
    transaction_id: txn.id
  }))
})

onMounted(() => {
  loadResults()
  categoriesStore.loadCategories()
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
      <div v-if="isTruncated" class="bg-status-warning text-on-dark alert" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        {{ $gettext('Too many transactions to display') }} — {{ $gettext('showing') }} {{ transactions.length }} / {{ totalTransactionCount }}. {{ $gettext('Select a result to see the rest.') }}
      </div>
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
