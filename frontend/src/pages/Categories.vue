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

// Account shape consumed by the template and the table builder helpers
interface AccountData {
  id: string
  formatted_id: string
  currency: string
}

// Month/category cell aggregate: running total plus popover detail lines
interface CellAggregate {
  total: number
  detailLines: string[]
}

// Precomputed account/category/month matrix for one account
interface AccountAggregate {
  id: string
  formatted_id: string
  currency: string
  months: string[]
  categories: string[]
  cells: Map<string, CellAggregate>
}

// Table columns and rows derived for one account
interface AccountTable {
  account: AccountData
  columns: Column[]
  rows: Record<string, unknown>[]
}

// Build the account/category/month matrix in a single pass over the
// transactions. Recomputed only when the transaction list changes;
// replaces per-cell filtering of the full dataset during rendering.
const accountAggregates = computed<AccountAggregate[]>(() => {
  const byAccount = new Map<string, {
    currency: string
    months: Set<string>
    categories: Set<string>
    cells: Map<string, CellAggregate>
  }>()

  for (const txn of transactions.value) {
    // vue-router rejects empty route params, so transactions without an
    // account are grouped under the backend's 'unknown' fallback ID
    const accountId = txn.account || 'unknown'
    const categoryId = txn.category_id || 'uncategorized'
    const monthKey = getMonthKey(txn.date)

    let account = byAccount.get(accountId)
    if (!account) {
      account = {
        currency: txn.currency,
        months: new Set(),
        categories: new Set(),
        cells: new Map()
      }
      byAccount.set(accountId, account)
    }

    account.months.add(monthKey)
    account.categories.add(categoryId)

    const cellKey = `${categoryId}|${monthKey}`
    let cell = account.cells.get(cellKey)
    if (!cell) {
      cell = { total: 0, detailLines: [] }
      account.cells.set(cellKey, cell)
    }
    cell.total += txn.amount || 0
    cell.detailLines.push(
      `${formatTransactionDate(txn.date)}: ${formatAmount(txn.amount)} - ${txn.original_partner || txn.partner || ''}`
    )
  }

  return Array.from(byAccount.entries()).map(([id, account]) => ({
    id,
    formatted_id: id,
    currency: account.currency,
    // Newest month first, categories in default sort order
    months: Array.from(account.months).sort((a, b) => b.localeCompare(a)),
    categories: Array.from(account.categories).sort(),
    cells: account.cells
  }))
})

// Month/category cell total from the precomputed matrix, or null when the
// cell has no transactions
function getCellTotal(
  aggregate: AccountAggregate,
  categoryId: string,
  monthKey: string
): number | null {
  return aggregate.cells.get(`${categoryId}|${monthKey}`)?.total ?? null
}

// Popover detail lines for a month/category cell as a single string
function getCellDetailsString(
  aggregate: AccountAggregate,
  categoryId: string,
  monthKey: string
): string {
  return aggregate.cells.get(`${categoryId}|${monthKey}`)?.detailLines.join('<br>') ?? ''
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
function buildTableColumnsFor(aggregate: AccountAggregate): Column[] {
  const accountId = aggregate.id

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
  for (const monthKey of aggregate.months) {
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
        const monthTotal = getCellTotal(aggregate, category_id, monthKey)

        if (monthTotal === null) {
          return { to: '#', children: '' }
        }

        if (!category_id) {
          return { to: '#', class: 'clickable', children: monthTotal }
        }

        const linkUrl = {
          name: 'category-month-transactions',
          params: { accountId, categoryId: category_id, monthId },
          query: buildResultQuery(resultId.value)
        }

        // For popover - details for this category and month are
        // precomputed with the cell aggregate
        const detailsContent = getCellDetailsString(aggregate, category_id, monthKey)

        return {
          to: linkUrl,
          class: 'clickable',
          children: monthTotal,
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
function buildTableRowsFor(aggregate: AccountAggregate): Record<string, unknown>[] {
  const data: Record<string, unknown>[] = []

  interface TableRow extends Record<string, unknown> {
    _rowIds: Record<string, string>
  }

  for (const category of aggregate.categories) {
    const row: TableRow = {
      category,
      category_id: category,
      accountId: aggregate.id,
      _rowIds: {}
    }

    for (const monthKey of aggregate.months) {
      const columnKey = `month-${monthKey}`
      row[columnKey] = getCellTotal(aggregate, category, monthKey) ?? 0
      row._rowIds[columnKey] = `${aggregate.id}|${monthKey}|${category}`
    }

    data.push(row)
  }

  return data
}

// Fully precomputed tables per account; the template renders directly
// from this cached structure
const accountTables = computed<AccountTable[]>(() => accountAggregates.value.map(aggregate => ({
  account: {
    id: aggregate.id,
    formatted_id: aggregate.formatted_id,
    currency: aggregate.currency
  },
  columns: buildTableColumnsFor(aggregate),
  rows: buildTableRowsFor(aggregate)
})))

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

      <div v-for="{ account, columns, rows } in accountTables" :key="account.id" class="mb-5">
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
              :data="rows"
              :columns="columns"
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
