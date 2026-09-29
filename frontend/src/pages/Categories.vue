<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import {
  fetchAllTransactions,
  fetchProcessingResultMetadata,
  recalculateStatistics
} from '../js/api.js'
import { buildResultQuery, extractResultId } from '../js/routeUtils.js'
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

// Optional resultId filter, carried in the query string
const resultId = computed(() => extractResultId(route.query as Record<string, unknown>))
const metadata = ref<ProcessingResultMetadata | null>(null)
const transactions = ref<TransactionListItem[]>([])
const totalTransactionCount = ref(0)
const isLoading = ref(true)
const error = ref<string | null>(null)

// The unfiltered view fetches with a limit; warn when rows were left out
const isTruncated = computed(() => totalTransactionCount.value > transactions.value.length)

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
    // vue-router rejects empty route params, so transactions without an
    // account are grouped under the backend's 'unknown' fallback ID
    const accountId = txn.account || 'unknown'
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
  try {
    // Fetch metadata only when scoped to a specific result
    metadata.value = resultId.value
      ? await fetchProcessingResultMetadata(resultId.value)
      : null

    // Fetch the complete dataset, optionally filtered by result
    const response = await fetchAllTransactions(resultId.value ?? undefined)
    transactions.value = response.transactions
    totalTransactionCount.value = response.total_count

    error.value = null
    isLoading.value = false

    await loadHighlights()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    feedback.showError('Failed to load results: ' + error.value)
    isLoading.value = false
  }
}

// Fetch statistical highlights for the matrix cells from the recalculate
// endpoint, keyed by cell ID '{account}|{month}|{category}'
const loadHighlights = async () => {
  statisticalStore.setHighlights({})
  if (transactions.value.length === 0) return

  try {
    const response = await recalculateStatistics(
      resultId.value ?? undefined,
      statisticalStore.algorithms,
      statisticalStore.direction
    )
    if (response?.highlights) {
      statisticalStore.setHighlights(response.highlights)
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    feedback.showError($gettext('Failed to load highlights') + ': ' + message)
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
          to: {
            name: 'category-months',
            params: { accountId, categoryId: category_id },
            query: buildResultQuery(resultId.value)
          },
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
      headerTo: {
        name: 'month-categories',
        params: { accountId, monthId },
        query: buildResultQuery(resultId.value)
      },
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

        const linkUrl = {
          name: 'category-month-transactions',
          params: { accountId, categoryId: category_id, monthId },
          query: buildResultQuery(resultId.value)
        }

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
      row._rowIds[columnKey] = `${account.id}|${monthKey}|${category}`
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
    amount: { display: formatAmount(txn.amount), raw: txn.amount || 0 },
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

function formatAmount(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return ''
  return amount.toFixed(2)
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

// Reload when the resultId query filter changes while the page is reused
watch(resultId, () => {
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

    <div v-else-if="metadata || transactions.length > 0">
      <div v-if="isTruncated" class="bg-status-warning text-on-dark alert" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        {{ $gettext('Too many transactions to display') }} — {{ $gettext('showing') }} {{ transactions.length }} / {{ totalTransactionCount }}. {{ $gettext('Select a result to see the rest.') }}
      </div>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">
          {{ $gettext('Categories') }}
          <span v-if="!resultId" class="text-secondary fs-5">({{ $gettext('All Transactions') }})</span>
        </h1>
        <div class="d-flex gap-2">
          <RouterLink
            to="/"
            class="btn bg-surface-base text-secondary border-secondary hover-bg-surface-secondary mt-3 mb-3 me-2"
          >
            {{ $gettext('Back to Form') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'details', query: buildResultQuery(resultId) }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3 me-2"
          >
            {{ $gettext('Transactions') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'pivot', query: buildResultQuery(resultId) }"
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
      <p>{{ $gettext('No transactions found') }}</p>
      <p>
        <router-link to="/import" class="alert-link">{{ $gettext('Please upload a CSV file first.') }}</router-link>
      </p>
    </div>
  </div>
</template>
