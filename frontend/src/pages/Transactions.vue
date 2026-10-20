<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { fetchAllTransactions, fetchProcessingResultMetadata } from '../js/api.js'
import { buildResultQuery, extractResultId } from '../js/routeUtils.js'
import { useCategoriesStore } from '../stores/categories.js'
import {
  useTransactionCorrections,
  editableCorrectionColumns,
  isCorrected,
  merchantOf,
  correctedRowIds,
  UNCATEGORIZED
} from '../composables/useTransactionCorrections.js'
import { formatDateISO } from '../js/dateUtils.js'
import VueDataTable from '../components/data/VueDataTable.vue'
import ToggleFilterButton from '../components/data/ToggleFilterButton.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import type {
  ProcessingResultMetadata,
  TransactionListItem
} from '../types/api.js'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const route = useRoute()

// Optional resultId filter, carried in the query string
const resultId = computed(() => extractResultId(route.query as Record<string, unknown>))

const transactions = ref<TransactionListItem[]>([])

// Persist corrections and undo them, refreshing the local row in place;
// errors are rethrown so the editing cell can display them inline
const { saveCorrection, undoCorrection, correctedCellHighlights } =
  useTransactionCorrections(() => transactions.value)

// Shared correctable columns (category, merchant, notice, undo)
const { categoryColumn, merchantColumn, noticeColumn, undoColumn } =
  editableCorrectionColumns($gettext, saveCorrection, undoCorrection)

// Toolbar view toggles (all default off)
const correctedOnly = ref(false)
const editMode = ref(false)
const showConfidence = ref(false)

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

// Table columns definition; the confidence column and the edit-mode
// undo column are toggled from the filter toolbar
const columns = computed<Column[]>(() => {
  const cols: Column[] = [
    { key: 'date', title: $gettext('Date') },
    categoryColumn(categoryFilterOptions.value),
    merchantColumn(),
    { key: 'amount', title: $gettext('Amount') },
    { key: 'currency', title: $gettext('Currency') },
    { key: 'account', title: $gettext('Account') },
    { key: 'type', title: $gettext('Type') }
  ]

  if (showConfidence.value) {
    cols.push({ key: 'confidence', title: $gettext('Confidence') })
  }

  cols.push(noticeColumn())

  if (editMode.value) {
    cols.push(undoColumn())
  }

  return cols
})

const metadata = ref<ProcessingResultMetadata | null>(null)
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

// Flatten all transactions for the data table, optionally limited to
// corrected transactions by the toolbar toggle
const allTransactions = computed(() => {
  const source = correctedOnly.value
    ? transactions.value.filter(isCorrected)
    : transactions.value
  return source.map(txn => ({
    date: formatDateISO(txn.date),
    category_id: txn.category_id || UNCATEGORIZED,
    merchant: merchantOf(txn),
    amount: txn.amount?.toFixed(2) || '',
    currency: txn.currency || '',
    account: txn.account,
    type: txn.transaction_type || '',
    confidence: txn.confidence?.toString() ?? '',
    notice: txn.notice || '',
    corrected: isCorrected(txn),
    row_id: String(txn.id),
    transaction_id: txn.id,
    _rowIds: correctedRowIds(txn)
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
            :cell-highlights-by-row-id="correctedCellHighlights"
            wrapper-class="w-auto"
            show-column-filters
            show-pagination
            :page-size="100"
            @cleared-filters="correctedOnly = false"
          >
            <template #filter-actions>
              <ToggleFilterButton
                v-model="correctedOnly"
                :label="$gettext('Corrected')"
                :title="$gettext('Show only transactions with corrections')"
              />
              <ToggleFilterButton
                v-model="editMode"
                :label="$gettext('Edit')"
                :title="$gettext('Show the column with correction actions')"
              />
              <ToggleFilterButton
                v-model="showConfidence"
                :label="$gettext('Confidence')"
                :title="$gettext('Show the confidence column')"
              />
            </template>
          </VueDataTable>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
