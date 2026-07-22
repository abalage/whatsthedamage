<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchResults as fetchResultsApi } from '../js/api.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useStatisticalStore } from '../stores/statistical.js'
import { useCategoriesStore } from '../stores/categories.js'
import { useGettext } from 'vue3-gettext'
import { useRoute, RouterLink } from 'vue-router'
import type { ResultsApiResponse, Account } from '../types/api.js'
import VueDataTable from '../components/data/VueDataTable.vue'
import TableLink from '../components/data/TableLink.vue'
import TableLinkWithPopover from '../components/data/TableLinkWithPopover.vue'
import type { Column } from '../components/data/VueDataTable.vue'
import { formatMonthYear } from '../js/dateUtils.js'

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
    // Fetch results data from the API endpoint we created
    const response = await fetchResultsApi(resultId.value)
    resultsData.value = response
    error.value = null

    // Initialize highlights in Pinia store
    if (response.highlights) {
      statisticalStore.setHighlights(response.highlights)
    }

    isLoading.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load results'
    feedback.showError('Failed to load results: ' + error.value)
    isLoading.value = false
  }
}

// Build column definitions for an account's table
function buildTableColumns(account: Account): Column[] {
  const accountId = account.id

  const columns: Column[] = [
    {
      key: 'category',
      title: $gettext('Categories'),
      sortable: true,
      component: TableLink,
      componentProps: (value: unknown, row?: Record<string, unknown>) => {
        const category_id = String(row?.category_id ?? '')
        const categoryId = getCategoryId(accountId, category_id) || category_id
        const categoryDisplayName = categoriesStore.getCategoryDisplayName(category_id)
        if (!categoryId) {
          return { to: '#', class: 'clickable', children: categoryDisplayName }
        }
        return {
          to: { name: 'category-months', params: { resultId: resultId.value, accountId, categoryId } },
          class: 'clickable',
          children: categoryDisplayName
        }
      }
    }
  ]

  // Add month columns
  for (const monthTs of getMonthsForAccount(account)) {
    const monthId = getMonthId(accountId, monthTs)
    columns.push({
      key: `month-${monthTs}`,
      title: formatMonthYear(monthTs),
      sortable: true,
      headerTo: { name: 'month-categories', params: { resultId: resultId.value, accountId, monthId } },
      component: TableLinkWithPopover,
      componentProps: (value: unknown, row?: Record<string, unknown>) => {
        const category_id = String(row?.category_id ?? row?.category ?? '')
        const monthData = buildCategoryMonthMap(account)[category_id]?.[monthTs]

        if (!monthData) {
          return { to: '#', children: '' }
        }

        const total = monthData.total?.display || ''
        const accountId = account.id
        const categoryId = getCategoryId(accountId, category_id) || category_id
        if (!categoryId || !monthId) {
          return { to: '#', class: 'clickable', children: total }
        }

        const linkUrl = { name: 'category-month-transactions', params: { resultId: resultId.value, accountId, categoryId, monthId } }

        // For popover
        const hasDetails = monthData.details && monthData.details.length > 0
        const detailsContent = hasDetails ? getDetailsString(monthData.details) : ''

        return {
          to: linkUrl,
          class: 'clickable',
          children: total,
          popoverContent: hasDetails ? detailsContent : undefined,
          popoverPlacement: 'top',
          popoverCustomClass: 'popover-wide'
        }
      }
    })
  }

  return columns
}

// Build table data for an account
function buildTableData(account: Account): Record<string, unknown>[] {
  const data: Record<string, unknown>[] = []
  const catMonthMap = buildCategoryMonthMap(account)
  const months = getMonthsForAccount(account)

  for (const category of Object.keys(catMonthMap).sort()) {
    interface TableRow extends Record<string, unknown> {
      _rowIds: Record<string, string>
    }
    const row: TableRow = {
      category,
      category_id: category,
      accountId: account.id,
      _rowIds: {}
    }

    for (const monthTs of months) {
      const monthData = catMonthMap[category]?.[monthTs]
      const columnKey = `month-${monthTs}`
      row[columnKey] = monthData?.total?.raw ?? 0

      // Store the API row_id for this cell
      if (monthData?.row_id) {
        row._rowIds[columnKey] = monthData.row_id
      }
    }

    data.push(row)
  }

  return data
}

// Get highlights for an account's table from Pinia store
function getAccountHighlights(): Record<string, string[]> {
  return statisticalStore.highlights || {}
}

const getMonthsForAccount = (account: Account) => {
  if (!account.data) return []
  const monthMap = new Map<number, number>()
  for (const row of account.data) {
    const monthField = row.date
    monthMap.set(monthField.timestamp, monthField.timestamp)
  }
  return Array.from(monthMap.values()).sort((a, b) => b - a)  
}

const buildCategoryMonthMap = (account: Account) => {
  const catMonthMap: Record<string, Record<number, any>> = {}

  if (!account.data) return catMonthMap

  for (const row of account.data) {
    if (!catMonthMap[row.category_id]) {
      catMonthMap[row.category_id] = {}
    }
    const monthKey = row.date.timestamp
    catMonthMap[row.category_id][monthKey] = row
  }

  return catMonthMap
}

const getDetailsString = (details: Array<{ date: { display: string }, amount: { display: string }, merchant: string }>): string => {
  return details
    .map(detail => `${detail.date.display}: ${detail.amount.display} - ${detail.merchant}`)
    .join('<br>')
}

/**
 * Get category ID from drilldown URLs for a specific account and category_id
 */
const getCategoryId = (accountId: string, category_id: string): string => {
  const urls = resultsData.value?.drilldown_urls_by_account[accountId]
  return urls?.category_urls?.[category_id]?.category_id || category_id
}

/**
 * Get month ID from drilldown URLs for a specific account and month timestamp
 */
const getMonthId = (accountId: string, monthTs: number): string => {
  const urls = resultsData.value?.drilldown_urls_by_account[accountId]
  return urls?.month_urls?.[String(monthTs)]?.month_id || String(monthTs)
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

    <div v-else-if="resultsData">
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

      <div v-for="account in resultsData.accounts" :key="account.id" class="mb-5">
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
