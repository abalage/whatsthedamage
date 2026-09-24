<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  fetchProcessingResultMetadata, 
  fetchTransactionsByResult
} from '../js/api.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useStatisticalStore } from '../stores/statistical.js'
import { useCategoriesStore } from '../stores/categories.js'
import { useGettext } from 'vue3-gettext'
import { useRoute, RouterLink } from 'vue-router'
import type { 
  ProcessingResultMetadata, 
  TransactionListItem
} from '../types/api.js'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import TableLinkWithPopover from '../components/data/TableLinkWithPopover.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import { formatMonthYear, createMonthDate, extractMonthKey, getMonthKey } from '../js/dateUtils.js'

// Helper function to format month key (YYYY-MM) to display format
function formatMonthKey(monthKey: string): string {
  const normalized = extractMonthKey(monthKey)
  const monthDate = createMonthDate(normalized)
  if (monthDate) {
    return formatMonthYear(monthDate.getTime() / 1000)
  }
  return monthKey
}

const { $gettext } = useGettext()

const feedback = useFeedbackStore()
const statisticalStore = useStatisticalStore()
const categoriesStore = useCategoriesStore()
const route = useRoute()

// Try both camelCase and snake_case for the query parameter
const resultId = computed(() => {
  const id = route.query.resultId ?? route.query.result_id
  return typeof id === 'string' ? id : null
})
const metadata = ref<ProcessingResultMetadata | null>(null)
const transactions = ref<TransactionListItem[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

// Interface for account data structure
interface AccountData {
  id: string
  formatted_id: string
  currency: string
  data: any[]
}

// Build account structure from transactions
const buildAccountsFromTransactions = (txns: TransactionListItem[]): AccountData[] => {
  const accountMap = new Map<string, AccountData>()
  
  for (const txn of txns) {
    const accountId = txn.account
    if (!accountMap.has(accountId)) {
      accountMap.set(accountId, {
        id: accountId,
        formatted_id: accountId,
        currency: txn.currency,
        data: []
      })
    }
  }
  
  // For now, we'll create a simplified structure
  // The full implementation would group transactions by account, category, and month
  return Array.from(accountMap.values())
}

const loadResults = async () => {
  if (!resultId.value) {
    error.value = 'No result ID provided'
    isLoading.value = false
    return
  }

  try {
    // Fetch metadata
    metadata.value = await fetchProcessingResultMetadata(resultId.value)
    
    // Fetch all transactions for this result
    const response = await fetchTransactionsByResult(resultId.value, { limit: 10000 })
    transactions.value = response.transactions
    
    // Initialize highlights in Pinia store
    if (metadata.value) {
      // For now, set empty highlights - they will be fetched per-group in the drilldown
      statisticalStore.setHighlights({})
    }

    error.value = null
    isLoading.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    feedback.showError('Failed to load results: ' + error.value)
    isLoading.value = false
  }
}

// Build column definitions for an account's table
function buildTableColumns(account: AccountData): Column[] {
  const accountId = account.id

  // Get all unique months from transactions for this account
  const accountTransactions = transactions.value.filter(t => t.account === accountId)
  const months = getMonthsFromTransactions(accountTransactions)

  const columns: Column[] = [
    {
      key: 'category',
      title: $gettext('Categories'),
      sortable: true,
      component: TableLink,
      componentProps: (value: unknown, row?: Record<string, unknown>) => {
        const category_id = String(row?.category_id ?? '')
        const categoryDisplayName = categoriesStore.getCategoryDisplayName(category_id)
        if (!category_id) {
          return { to: '#', class: 'clickable', children: categoryDisplayName }
        }
        return {
          to: { name: 'category-months', params: { resultId: resultId.value, accountId, categoryId: category_id } },
          class: 'clickable',
          children: categoryDisplayName
        }
      }
    }
  ]

  // Add month columns
  for (const monthKey of months) {
    const monthId = monthKey
    columns.push({
      key: `month-${monthKey}`,
      title: formatMonthKey(monthKey),
      sortable: true,
      headerTo: { name: 'month-categories', params: { resultId: resultId.value, accountId, monthId } },
      component: TableLinkWithPopover,
      componentProps: (value: unknown, row?: Record<string, unknown>) => {
        const category_id = String(row?.category_id ?? '')
        const monthTotal = getMonthTotalForCategory(accountId, category_id, monthKey)

        if (monthTotal === undefined || monthTotal === null) {
          return { to: '#', children: '' }
        }

        const total = monthTotal
        if (!category_id) {
          return { to: '#', class: 'clickable', children: total }
        }

        const linkUrl = { name: 'category-month-transactions', params: { resultId: resultId.value, accountId, categoryId: category_id, monthId } }

        // For popover - get details for this category and month
        const details = getTransactionDetailsForCategoryMonth(accountId, category_id, monthKey)
        const detailsContent = details.length > 0 ? getDetailsString(details) : ''

        return {
          to: linkUrl,
          class: 'clickable',
          children: total,
          popoverContent: detailsContent || undefined,
          popoverPlacement: 'top',
          popoverCustomClass: 'popover-wide'
        }
      }
    })
  }

  return columns
}

// Build table data for an account
function buildTableData(account: AccountData): Record<string, unknown>[] {
  const data: Record<string, unknown>[] = []
  const accountTransactions = transactions.value.filter(t => t.account === account.id)
  const categories = getCategoriesFromTransactions(accountTransactions)
  const months = getMonthsFromTransactions(accountTransactions)

  for (const category of categories.sort()) {
    interface TableRow extends Record<string, unknown> {
      _rowIds: Record<string, string>
    }
    const row: TableRow = {
      category,
      category_id: category,
      accountId: account.id,
      _rowIds: {}
    }

    for (const monthKey of months) {
      const columnKey = `month-${monthKey}`
      const monthTotal = getMonthTotalForCategory(account.id, category, monthKey)
      row[columnKey] = monthTotal ?? 0
    }

    data.push(row)
  }

  return data
}

// Helper functions for new data structure
function getMonthsFromTransactions(txns: TransactionListItem[]): string[] {
  const months = new Set<string>()
  for (const txn of txns) {
    // Extract YYYY-MM from date (handle both timestamp and ISO format)
    const monthKey = getMonthKeyFromTransactionDate(txn.date)
    months.add(monthKey)
  }
  return Array.from(months).sort((a, b) => b.localeCompare(a)) // Newest first
}

// Helper to extract month key from transaction date (handles both ISO string and timestamp)
// Uses the new utility function that handles both formats
function getMonthKeyFromTransactionDate(dateValue: string | undefined): string {
  return getMonthKey(dateValue)
}

function getCategoriesFromTransactions(txns: TransactionListItem[]): string[] {
  const categories = new Set<string>()
  for (const txn of txns) {
    const cat = txn.category_id || 'uncategorized'
    categories.add(cat)
  }
  return Array.from(categories)
}

function getMonthTotalForCategory(accountId: string, categoryId: string, monthKey: string): number | null {
  const accountTxns = transactions.value.filter(
    t => t.account === accountId && 
         (t.category_id || 'uncategorized') === categoryId &&
         getMonthKeyFromTransactionDate(t.date) === monthKey
  )
  
  if (accountTxns.length === 0) return null
  
  const total = accountTxns.reduce((sum, txn) => sum + (txn.amount || 0), 0)
  return total
}

function getTransactionDetailsForCategoryMonth(accountId: string, categoryId: string, monthKey: string) {
  const accountTxns = transactions.value.filter(
    t => t.account === accountId && 
         (t.category_id || 'uncategorized') === categoryId &&
         getMonthKeyFromTransactionDate(t.date) === monthKey
  )
  
  return accountTxns.map(txn => ({
    date: { display: formatTransactionDate(txn.date) },
    amount: { display: formatAmount(txn.amount, txn.currency), raw: txn.amount || 0 },
    merchant: txn.original_partner || txn.partner || ''
  }))
}

// Helper to format transaction date for display (handle timestamp or ISO string)
function formatTransactionDate(dateValue: string | undefined): string {
  if (!dateValue || typeof dateValue !== 'string') {
    return ''
  }
  
  // If it's a numeric string (timestamp), convert to locale date string
  if (/^\d+$/.test(dateValue)) {
    const timestamp = parseInt(dateValue, 10)
    if (!Number.isNaN(timestamp)) {
      // Use the existing formatMonthYear for consistency
      return formatMonthYear(timestamp)
    }
  }
  
  // Otherwise, return as-is (it's already a formatted string)
  return dateValue
}

function formatAmount(amount: number | null | undefined, currency: string | null | undefined): string {
  if (amount === null || amount === undefined) return ''
  return `${currency || ''} ${amount.toFixed(2)}`
}

// Get highlights for an account's table from Pinia store
function getAccountHighlights(): Record<string, string[]> {
  return statisticalStore.highlights || {}
}

// Keep the old getDetailsString for compatibility
const getDetailsString = (details: Array<{ date: { display: string }, amount: { display: string }, merchant: string }>): string => {
  return details
    .map(detail => `${detail.date.display}: ${detail.amount.display} - ${detail.merchant}`)
    .join('<br>')
}

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="container-fluid">
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Categories') }}</li>
      </ol>
    </nav>

    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-on-primary">
        <span class="visually-hidden">{{ $gettext('loading') }}...</span>
      </output>
      <p class="mt-2">{{ $gettext('Loading results') }}...</p>
    </div>

    <div v-else-if="error" class="bg-status-danger text-on-light alert">
      {{ error }}
    </div>

    <div v-else-if="metadata">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ $gettext('Categories') }}</h1>
        <div class="d-flex gap-2">
          <RouterLink
            to="/"
            class="btn bg-surface-base text-secondary border-secondary hover-bg-surface-secondary mt-3 mb-3 me-2"
          >
            {{ $gettext('Back to Form') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'details', params: { resultId: resultId } }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3 me-2"
          >
            {{ $gettext('Transactions') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'pivot', params: { resultId: resultId } }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Pivot Table') }}
          </RouterLink>
        </div>
      </div>

      <div v-for="account in buildAccountsFromTransactions(transactions)" :key="account.id" class="mb-5">
        <div class="card mb-4" style="width: 100%; margin: 0 auto">
          <div class="card-header">
            {{ $gettext('Account') }}: {{ account.formatted_id }}
            <span v-if="account.currency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
              {{ account.currency }}
            </span>
          </div>
          <div class="card-body">
            <VueDataTable
              :id="`datatable-${account.id}`"
              :data="buildTableData(account)"
              :columns="buildTableColumns(account)"
              :cell-highlights-by-row-id="getAccountHighlights()"
              :csv-text="$gettext('Export CSV')"
              :excel-text="$gettext('Export Excel')"
              wrapper-class="w-auto"
              show-column-filters
              show-pagination
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else class="bg-status-info text-on-light alert">
      <p>{{ $gettext('No results found') }}</p>
      <p v-if="!resultId">
        {{ $gettext('No result ID was provided.') }}
        <router-link to="/" class="alert-link">{{ $gettext('Please upload a CSV file first.') }}</router-link>
      </p>
    </div>
  </div>
</template>
