<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useCategoriesStore } from '../stores/categories'
import { useDrilldownData } from '../composables/useDrilldownData'
import { RouterLink } from 'vue-router'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import type { BreadcrumbItem } from '../composables/useBreadcrumbs'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VueDataTable from '../components/data/VueDataTable.vue'
import ToggleFilterButton from '../components/data/ToggleFilterButton.vue'
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue'
import { fetchCategoryMonthTransactions } from '../js/api'
import { useResultQuery } from '../composables/useResultQuery'
import {
  useTransactionCorrections,
  editableCorrectionColumns,
  isCorrected,
  merchantOf,
  correctedRowIds,
  UNCATEGORIZED
} from '../composables/useTransactionCorrections'
import type { TransactionListResponse } from '../types/api'
import { formatMonthYear, formatDateISO, toEpoch } from '../js/dateUtils'
import BarChart from '../components/charts/BarChart.vue'

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()

// Optional resultId filter, carried in the query string
const resultQuery = useResultQuery()

const {
  data: transactionsData,
  isLoading,
  error,
  fetchData,
  resultId,
  accountId,
  pageTitle,
  breadcrumbItems
} = useDrilldownData<TransactionListResponse>({
  fetchData: async (params) => {
    if (!params.accountId || !params.categoryId || !params.monthId) {
      throw new Error('Missing required parameters for category month transactions fetch')
    }
    return fetchCategoryMonthTransactions(params)
  },
  titleBaseKey: 'Transactions',
  titleFormat: 'category-month',
  titleExtractor: (data: TransactionListResponse) => {
    const firstTxn = data.transactions[0]
    const monthTimestamp = firstTxn ? toEpoch(firstTxn.date) : 0
    return {
      categoryId: firstTxn?.category_id ?? undefined,
      monthTimestamp
    }
  },
  breadcrumbItems: (data: TransactionListResponse | null): BreadcrumbItem[] => {
    // Extract category and month from first transaction
    const firstTxn = data?.transactions[0]
    const categoryName = firstTxn ? categoriesStore.getCategoryDisplayName(firstTxn.category_id || '') : null
    const monthTimestamp = firstTxn ? toEpoch(firstTxn.date) : null
    const monthName = monthTimestamp !== null ? formatMonthYear(monthTimestamp) : null
    return [
      { name: $gettext('Home'), to: '/' },
      { name: $gettext('Categories'), to: { name: 'results', query: resultQuery() } },
      { name: categoryName && monthName ? `${categoryName} - ${monthName}` : $gettext('Transaction Details'), active: true }
    ]
  },
})

// Persist corrections and undo them, refreshing the local row in place;
// errors are rethrown so the editing cell can display them inline
const { saveCorrection, undoCorrection, correctedCellHighlights } =
  useTransactionCorrections(() => transactionsData.value?.transactions ?? [])

// Shared correctable columns (category, merchant, notice, undo)
const { categoryColumn, merchantColumn, noticeColumn, undoColumn } =
  editableCorrectionColumns($gettext, saveCorrection, undoCorrection)

// Toolbar view toggles (default off)
const correctedOnly = ref(false)
const editMode = ref(false)

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

// Table columns; the edit-mode undo column is toggled from the toolbar
const columns = computed<Column[]>(() => {
  const cols: Column[] = [
    { key: 'date', title: $gettext('Date'), formatValue: (value: unknown, row?: Record<string, unknown>) => String(((row as { date_display?: string })?.date_display) || value || '') },
    categoryColumn(categoryFilterOptions.value),
    merchantColumn(),
    {
      key: 'amount',
      title: $gettext('Amount'),
      formatValue: (value: unknown, row?: Record<string, unknown>) => String(((row as { amount_display?: string })?.amount_display) || value || '')
    },
    noticeColumn()
  ]

  if (editMode.value) {
    cols.push(undoColumn())
  }

  return cols
})

// Extract account currency from first transaction
const accountCurrency = computed(() => {
  if (!transactionsData.value?.transactions || transactionsData.value.transactions.length === 0) return null
  const firstTxn = transactionsData.value.transactions[0]
  return firstTxn.currency || null
})

// Table data, optionally limited to corrected transactions by the
// toolbar toggle
const tableData = computed(() => {
  const rows = (transactionsData.value?.transactions ?? []).map(t => ({
    date: t.date,
    date_display: formatDateISO(t.date),
    category_id: t.category_id || UNCATEGORIZED,
    merchant: merchantOf(t),
    amount: t.amount,
    amount_display: t.amount.toFixed(2),
    notice: t.notice || '',
    corrected: isCorrected(t),
    row_id: String(t.id),
    transaction_id: t.id,
    _rowIds: correctedRowIds(t)
  }))
  return correctedOnly.value ? rows.filter(row => row.corrected) : rows
})

// Aggregate row configuration for the table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!transactionsData.value || transactionsData.value.transactions.length === 0) return []

  return [
    {
      id: 'amount-sum',
      type: 'custom',
      position: 'footer',
      class: 'fw-bold bg-surface-primary text-on-primary',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'date') return $gettext('Total')
        if (columnKey === 'amount') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.reduce((sum, val) => sum + val, 0)
        }
        return ''
      }
    },
    {
      id: 'amount-average',
      type: 'custom',
      position: 'footer',
      class: 'fw-bold bg-surface-secondary text-on-dark',
      customCalculator: (data, columnKey) => {
        if (columnKey === 'date') return $gettext('Average')
        if (columnKey === 'amount') {
          const numericValues = data.map(row => Number(row[columnKey])).filter(v => !Number.isNaN(v))
          return numericValues.length > 0
            ? numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length
            : null
        }
        return ''
      }
    }
  ]
})

// Chart data for BarChart
const chartData = computed(() => {
  return tableData.value.map(row => ({
    label: row.date_display,
    timestamp: row.date ? parseInt(row.date, 10) : 0,
    values: { amount: row.amount as number }
  }))
})

const chartCategories = computed(() => [
  { id: 'amount', label: $gettext('Amount') }
])

onMounted(() => {
  fetchData()
  categoriesStore.loadCategories()
})

// Refetch when the resultId query filter changes while the page is reused
watch(resultId, () => {
  fetchData()
})
</script>

<template>
  <div class="container-fluid">
    <BreadcrumbNavigation :items="breadcrumbItems" />

    <LoadingState v-if="isLoading" />

    <ErrorState v-else-if="error" :message="error" />

    <!-- Main Content -->
    <div v-else-if="transactionsData">
      <PageHeader :title="pageTitle">
        <template #actions>
          <div class="d-flex gap-2">
            <RouterLink
              :to="{ name: 'results', query: resultQuery() }"
              class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
            >
              {{ $gettext('Back to Categories') }}
            </RouterLink>
          </div>
        </template>
      </PageHeader>

      <!-- Cards Container -->
      <div class="d-flex gap-4 flex-wrap justify-content-center">
        <!-- Account & Table Card -->
        <div class="card flex-grow-1" style="min-width: 400px">
          <div class="card-header">
            {{ $gettext('Account') }}: {{ accountId || $gettext('Unknown') }}
            <span v-if="accountCurrency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">
              {{ accountCurrency }}
            </span>
          </div>
          <div class="card-body">
            <VueDataTable
              id="transaction-details-table"
              :data="tableData"
              :columns="columns"
              :aggregate-rows="aggregateRows"
              :cell-highlights-by-row-id="correctedCellHighlights"
              wrapper-class="w-auto"
              show-column-filters
              show-pagination
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
              </template>
            </VueDataTable>
          </div>
        </div>

        <!-- Chart Card -->
        <div class="card flex-grow-1" style="min-width: 400px">
          <div class="card-header">
            {{ $gettext('Transactions') }}
          </div>
          <div class="card-body">
            <BarChart
              :data="chartData"
              :categories="chartCategories"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="bg-status-info text-on-light alert">
      {{ $gettext('No transactions found') }}
    </div>
  </div>
</template>
