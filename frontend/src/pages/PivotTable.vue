<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { fetchTransactionsByResult } from '../js/api.js';
import { useFeedbackStore } from '../stores/feedback.js';
import { useGettext } from 'vue3-gettext';
import { usePivotStore } from '../stores/pivot.js';
import { useCategoriesStore } from '../stores/categories.js';
import type { Account, TransactionListItem, ResultsApiResponse } from '../types/api.js';
import type { BreadcrumbItem } from '../composables/useBreadcrumbs.js'
import BarChart from '../components/charts/BarChart.vue';
import PivotCategorySelector from '../components/PivotCategorySelector.vue';
import PageHeader from '../components/layout/PageHeader.vue'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'

// VueDataTable component
import VueDataTable from '../components/data/VueDataTable.vue';
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue';
import { createMonthDate, getMonthKey } from '../js/dateUtils.js';

const { $gettext } = useGettext();
const feedback = useFeedbackStore();
const route = useRoute();
const pivotStore = usePivotStore();
const categoriesStore = useCategoriesStore();

const resultId = computed(() => route.params.resultId as string);
const isLoading = ref(true);

// Helper to extract month key from transaction date (handles both ISO string and timestamp)
// Uses the new utility function that handles both formats
function getMonthKeyFromTxnDate(dateValue: string | undefined): string {
  return getMonthKey(dateValue)
}
const error = ref<string | null>(null);

// Breadcrumb items
const breadcrumbItems = computed<BreadcrumbItem[]>(() => [
  { name: $gettext('Home'), to: '/' },
  { name: $gettext('Categories'), to: { name: 'results', query: { resultId: resultId.value } } },
  { name: $gettext('Pivot Table'), active: true }
]);

// Constants
const ZERO = 0;

/**
 * Transform flat transaction list into ResultsApiResponse format for pivot store
 */
function transformToResultsApiResponse(
  transactions: TransactionListItem[],
  resultId: string
): ResultsApiResponse {
  // Group transactions by account
  const accountsMap = new Map<string, TransactionListItem[]>();
  for (const txn of transactions) {
    const accountId = txn.account;
    if (!accountsMap.has(accountId)) {
      accountsMap.set(accountId, []);
    }
    accountsMap.get(accountId)!.push(txn);
  }

  // Build accounts array
  const accounts: Account[] = [];
  for (const [accountId, accountTransactions] of accountsMap) {
    // Get account info from first transaction
    const firstTxn = accountTransactions[0];
    const account: Account = {
      id: accountId,
      name: accountId,
      formatted_id: accountId,
      currency: firstTxn.currency || '',
      data: [],
      result_id: resultId,
      metadata: null
    };

    // Group transactions by category_id and month (YYYY-MM)
    const categoryMonthMap = new Map<string, Map<string, TransactionListItem[]>>();
    for (const txn of accountTransactions) {
      const categoryId = txn.category_id || 'uncategorized';
      const monthKey = getMonthKeyFromTxnDate(txn.date);

      if (!categoryMonthMap.has(categoryId)) {
        categoryMonthMap.set(categoryId, new Map());
      }
      const monthMap = categoryMonthMap.get(categoryId)!;
      if (!monthMap.has(monthKey)) {
        monthMap.set(monthKey, []);
      }
      monthMap.get(monthKey)!.push(txn);
    }

    // Build aggregated rows
    for (const [categoryId, monthMap] of categoryMonthMap) {
      for (const [monthKey, monthTransactions] of monthMap) {
        const totalAmount = monthTransactions.reduce((sum, txn) => sum + (txn.amount || 0), 0);
        const monthDate = createMonthDate(monthKey);

        if (!monthDate) {
          continue; // Skip invalid dates
        }

        account.data!.push({
          row_id: `${accountId}-${categoryId}-${monthKey}`,
          category_id: categoryId,
          total: {
            display: `${firstTxn.currency || ''} ${totalAmount.toFixed(2)}`,
            raw: totalAmount
          },
          date: monthKey,  // ISO date string (YYYY-MM-DD)
          details: monthTransactions.map(txn => ({
            row_id: String(txn.id),
            date: txn.date || '',  // ISO date string from API
            amount: {
              display: `${txn.currency || ''} ${(txn.amount || 0).toFixed(2)}`,
              raw: txn.amount || 0
            },
            merchant: txn.original_partner || txn.partner || '',
            currency: txn.currency || '',
            account: txn.account,
            type: txn.transaction_type || null,
            confidence: txn.confidence || null,
            notice: txn.notice || null,
            category_id: txn.category_id || null,
            month_id: monthKey
          })),
          is_calculated: false
        });
      }
    }

    accounts.push(account);
  }

  return {
    result_id: resultId,
    accounts,
    highlights: {},
    drilldown_urls_by_account: {}
  };
}

const loadData = async () => {
  if (!resultId.value) {
    error.value = 'Missing result ID';
    isLoading.value = false;
    return;
  }

  try {
    // Fetch all transactions for this result
    const response = await fetchTransactionsByResult(resultId.value, { limit: 10000 });
    
    // Transform to ResultsApiResponse format for pivot store
    const resultsData = transformToResultsApiResponse(response.transactions, resultId.value);
    
    await categoriesStore.loadCategories();
    await categoriesStore.loadCostOfLivingCategories();
    pivotStore.setResultsData(resultsData);
    pivotStore.loadSettings();

    // If no account is selected, select the first one
    if (!selectedAccountId.value && resultsData.accounts.length > ZERO) {
      pivotStore.setSelectedAccountId(resultsData.accounts[ZERO].id);
    }

    isLoading.value = false;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load data';
    feedback.showError('Failed to load Pivot data: ' + error.value);
    isLoading.value = false;
  }
};

// Computed from store
const pivotData = computed(() => pivotStore.pivotData);
const resultsData = computed(() => pivotStore.resultsData);
const selectedAccountId = computed({
  get: () => pivotStore.selectedAccountId,
  set: (value: string) => pivotStore.setSelectedAccountId(value)
});
const selectedCategories = computed(() => pivotStore.selectedCategoryIds);
const availableCategories = computed(() => pivotStore.availableCategoryNames);
const accounts = computed<Account[]>(() => resultsData.value?.accounts || []);

// Chart data format for BarChart with stacked categories
const chartData = computed(() => {
  if (!pivotData.value) return [];
  return pivotData.value.months.map(month => ({
    label: month.month,  // month is already formatted (YYYY-MM)
    timestamp: month.month_timestamp,
    values: Object.fromEntries(
      Object.entries(month.categories).map(([catId, data]) => [
        catId,
        data?.amount || ZERO
      ])
    )
  }));
});

const trendlineValue = computed(() => pivotData.value?.mean ?? ZERO);

// Safe access to months for DataTable footer calculations
const safeMonths = computed(() => pivotData.value?.months || []);

// Handle selection changes from BarChart
const handleSelectionChanged = (payload: { selectedIndices: number[]; selectedItems: Array<{ index: number; label: string; values: Record<string, number>; total: number }>; changedIndex: number; isSelected: boolean }) => {
  console.log('Selection changed:', payload);
  // Extension point for future functionality
  // payload contains: selectedIndices, selectedItems, changedIndex, isSelected
  // Could show additional details, filter data, etc.
};

// Use categories store to get proper display name with translation
const getCategoryDisplayName = (categoryId: string): string => categoriesStore.getCategoryDisplayName(categoryId);

// NEW: Table column definitions for VueDataTable
const tableColumns = computed<Column[]>(() => {
  const columns: Column[] = [
    {
      key: 'month',
      title: $gettext('Month'),
      class: 'text-nowrap',
      sortable: true
    },
    {
      key: 'total',
      title: $gettext('Summary of Categories'),
      class: 'text-nowrap text-end',
      sortable: true,
      renderHtml: (value: unknown) => `${Math.abs(Number(value))}`
    }
  ];

  // Add columns for each selected category
  selectedCategories.value.forEach(catId => {
    columns.push({
      key: catId,
      title: getCategoryDisplayName(catId),
      class: 'text-nowrap text-end',
      sortable: true,
      renderHtml: (value: unknown) => {
        const amount = typeof value === 'number' ? value : (value as { amount: number } | null)?.amount ?? ZERO;
        return `${Math.abs(amount)}`;
      }
    });
  });

  return columns;
});

// NEW: Table data for VueDataTable
const tableData = computed<Record<string, unknown>[]>(() => {
  if (!pivotData.value) return [];

  return pivotData.value.months.map(month => {
    const row: Record<string, unknown> = {
      month: month.month,  // month is already formatted (YYYY-MM)
      total: month.total,
      row_id: month.month_timestamp // Use timestamp as row_id for highlighting
    };

    // Add category data for each selected category
    selectedCategories.value.forEach(catId => {
      row[catId] = month.categories[catId]?.amount ?? ZERO;
    });

    return row;
  });
});

// Aggregate row configuration for the data table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!pivotData.value || safeMonths.value.length === ZERO) return [];

  return [
    {
      id: 'average',
      label: $gettext('Average'),
      type: 'custom',
      position: 'footer',
      includeInExport: true,
      customCalculator: (data, columnKey) => {
        if (columnKey === 'month') return $gettext('Average');
        if (columnKey === 'total') return trendlineValue.value;

        const values = data.map(row => {
          const val = row[columnKey];
          return typeof val === 'number' ? Math.abs(val) : 0;
        });
        return values.reduce((sum, val) => sum + val, 0) / values.length;
      }
    }
  ];
});

// Auto-save settings
watch(() => [pivotStore.selectedCategoryIds, pivotStore.showTrendline], () => {
  pivotStore.saveSettings();
}, { deep: true });

onMounted(() => loadData());
</script>

<template>
  <div class="container-fluid">
    <BreadcrumbNavigation :items="breadcrumbItems" />

    <LoadingState v-if="isLoading" />

    <ErrorState v-else-if="error" :message="error" />

    <!-- Main Content -->
    <div v-else-if="resultsData">
      <PageHeader :title="$gettext('Pivot Table')">
        <template #actions>
          <RouterLink
            :to="{ name: 'results', query: { resultId: resultId } }"
            class="btn bg-surface-secondary text-on-dark border-secondary mt-3 mb-3"
          >
            {{ $gettext('Back to Categories') }}
          </RouterLink>
        </template>
      </PageHeader>

      <!-- Account Selector -->
      <div v-if="accounts.length > 1" class="mb-4">
        <div class="card" style="width: auto; margin: 0 auto">
          <div class="card-header">
            {{ $gettext('Select Account') }}
          </div>
          <div class="card-body">
            <label for="selectedAccountId" class="form-label">{{ $gettext('Account') }}</label>
            <select id="selectedAccountId" v-model="selectedAccountId" class="form-select">
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.formatted_id }} ({{ account.currency }})
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Category Selector -->
      <PivotCategorySelector v-if="availableCategories.length > 0" />

      <div v-else class="bg-status-warning text-on-dark alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i> {{ $gettext('No categories found in the data') }}
      </div>

      <div v-if="selectedCategories.length === 0 && availableCategories.length > 0" class="bg-status-info text-on-light alert mb-4">
        <i class="bi bi-info-circle me-2"></i> {{ $gettext('Please select at least one category to see calculations') }}
      </div>

      <!-- Summary -->
      <div v-if="pivotData && selectedCategories.length > 0" class="mb-4">
        <div class="card mb-4" style="width: auto; margin: 0 auto">
          <div class="card-header">
            {{ $gettext('Summary') }}
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <div class="d-flex justify-content-between mb-2">
                  <span><i class="bi bi-tags me-2"></i> {{ $gettext('Selected Categories') }}:</span>
                  <strong>{{ selectedCategories.length }}</strong>
                </div>
                <div class="selected-categories-list small text-secondary">{{ selectedCategories.map(getCategoryDisplayName).join(', ') }}</div>
              </div>
              <div class="col-md-6">
                <div class="d-flex justify-content-between mb-2">
                  <span><i class="bi bi-calendar me-2"></i> {{ $gettext('Months Analyzed') }}:</span>
                  <strong>{{ safeMonths.length }}</strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span><i class="bi bi-graph-up me-2"></i> {{ $gettext('Average Monthly') }}:</span>
                  <strong>{{ trendlineValue }}</strong>
                </div>
                <div class="d-flex justify-content-between">
                  <span><i class="bi bi-wallet2 me-2"></i> {{ $gettext('Total') }}:</span>
                  <strong>{{ safeMonths.reduce((sum, m) => sum + Math.abs(m.total), 0) }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bar Chart -->
      <div v-if="pivotData && selectedCategories.length > 0" class="mb-4">
        <div class="card mb-4" style="width: auto; margin: 0 auto">
          <div class="card-header">
            {{ $gettext('Monthly breakdown of selected categories') }}
          </div>
          <div class="card-body">
            <div class="form-check form-switch mb-0">
              <input id="showTrendline" v-model="pivotStore.showTrendline" class="form-check-input" type="checkbox" />
              <label class="form-check-label" for="showTrendline">{{ $gettext('Show trendline') }}</label>
            </div>
            <div class="chart-wrapper">
              <BarChart
                :data="chartData"
                :categories="selectedCategories.map(id => ({ id, label: getCategoryDisplayName(id) }))"
                :title="$gettext('Summaries of selected categories')"
                :show-trendline="pivotStore.showTrendline"
                :selectable="true"
                @selection-changed="handleSelectionChanged"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Data Table - VueDataTable component -->
      <div v-if="pivotData && selectedCategories.length > 0">
        <div class="card mb-4" style="width: auto; margin: 0 auto">
          <div class="card-header">
            {{ $gettext('Detailed Monthly Data') }}
          </div>
          <div class="card-body">
            <VueDataTable
              id="pivot-table"
              :key="`columns-${selectedCategories.join(',')}-${pivotData?.months.length}`"
              :columns="tableColumns"
              :data="tableData"
              :aggregate-rows="aggregateRows"
              aggregate-footer-row-class="bg-surface-primary text-on-primary fw-bold"
              :page-size="25"
              :csv-text="$gettext('Export CSV')"
              :excel-text="$gettext('Export Excel')"
              :search-placeholder="$gettext('Search') + ': '"
              wrapper-class="w-auto"
              show-column-filters
              show-pagination
              class="small"
            />
          </div>
        </div>
      </div>

      <div v-if="!pivotData && !isLoading" class="bg-status-info text-on-light alert">
        <i class="bi bi-inbox me-2"></i> {{ $gettext('No data available') }}
      </div>
    </div>

    <div v-else class="bg-status-info text-on-light alert">
      <i class="bi bi-inbox me-2"></i> {{ $gettext('No data available') }}
    </div>
  </div>
</template>
