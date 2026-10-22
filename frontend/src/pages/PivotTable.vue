<script setup lang="ts">
import { onMounted, computed, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { buildResultQuery, extractResultId } from '../js/routeUtils';
import { transformToResultsApiResponse } from '../js/resultsTransform';
import { useApiData } from '../composables/useApiData';
import { useDatasetStore, type DatasetEntry } from '../stores/dataset';
import { useGettext } from 'vue3-gettext';
import { usePivotStore } from '../stores/pivot';
import { useCategoriesStore } from '../stores/categories';
import type { Account } from '../types/api';
import type { BreadcrumbItem } from '../composables/useBreadcrumbs'
import BarChart from '../components/charts/BarChart.vue';
import PivotCategorySelector from '../components/PivotCategorySelector.vue';
import PageHeader from '../components/layout/PageHeader.vue'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'

// VueDataTable component
import VueDataTable from '../components/data/VueDataTable.vue';
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue';

const { $gettext } = useGettext();
const route = useRoute();
const datasetStore = useDatasetStore();
const pivotStore = usePivotStore();
const categoriesStore = useCategoriesStore();

const resultId = computed(() => extractResultId(route.query as Record<string, unknown>));

// Breadcrumb items
const breadcrumbItems = computed<BreadcrumbItem[]>(() => [
  { name: $gettext('Home'), to: '/' },
  { name: $gettext('Categories'), to: { name: 'results', query: buildResultQuery(resultId.value) } },
  { name: $gettext('Pivot Table'), active: true }
]);

// Fetch the dataset through the shared, cached store: navigating here
// from Categories or Transactions resolves instantly
const {
  data: fetchResponse,
  isLoading,
  error,
  fetchData: loadFetchedData
} = useApiData<DatasetEntry>({
  fetchFn: () => datasetStore.load(resultId.value ?? undefined),
  t: (key: string) => $gettext(key),
  errorMessageKey: 'Failed to load Pivot data'
});

const fetchedCount = computed(() => fetchResponse.value?.transactions.length ?? 0);
const totalTransactionCount = computed(() => fetchResponse.value?.total_count ?? 0);

// The unfiltered view fetches with a limit; warn when rows were left out
const isTruncated = computed(() => totalTransactionCount.value > fetchedCount.value);

/**
 * Load the dataset and populate the pivot store from the transformed
 * account/category/month aggregation
 */
const loadData = async () => {
  await loadFetchedData();
  const entry = fetchResponse.value;
  if (!entry) {
    return;
  }

  // Transform to ResultsApiResponse format for pivot store
  const resultsData = transformToResultsApiResponse(entry.transactions);

  await categoriesStore.loadCategories();
  await categoriesStore.loadCostOfLivingCategories();
  pivotStore.setResultsData(resultsData);

  // If no account is selected, select the first one
  if (!selectedAccountId.value && resultsData.accounts.length > 0) {
    pivotStore.setSelectedAccountId(resultsData.accounts[0].id);
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
        data?.amount || 0
      ])
    )
  }));
});

const trendlineValue = computed(() => pivotData.value?.mean ?? 0);

// Safe access to months for DataTable footer calculations
const safeMonths = computed(() => pivotData.value?.months || []);

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
        const amount = typeof value === 'number' ? value : (value as { amount: number } | null)?.amount ?? 0;
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
      row[catId] = month.categories[catId]?.amount ?? 0;
    });

    return row;
  });
});

// Aggregate row configuration for the data table
const aggregateRows = computed<AggregateRowConfig[]>(() => {
  if (!pivotData.value || safeMonths.value.length === 0) return [];

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

// Header title reflects whether all transactions or a specific result is shown
const headerTitle = computed(() =>
  resultId.value
    ? $gettext('Pivot Table')
    : `${$gettext('Pivot Table')} (${$gettext('All Transactions')})`
);

// Reload when the resultId query filter changes while the page is reused
watch(resultId, () => {
  loadData();
});

onMounted(() => loadData());
</script>

<template>
  <div class="container-fluid">
    <BreadcrumbNavigation :items="breadcrumbItems" />

    <LoadingState v-if="isLoading" />

    <ErrorState v-else-if="error" :message="error" />

    <!-- Main Content -->
    <div v-else-if="resultsData">
      <div v-if="isTruncated" class="bg-status-warning text-on-dark alert" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        {{ $gettext('Too many transactions to display') }} — {{ $gettext('showing') }} {{ fetchedCount }} / {{ totalTransactionCount }}. {{ $gettext('Select a result to see the rest.') }}
      </div>
      <PageHeader :title="headerTitle">
        <template #actions>
          <RouterLink
            :to="{ name: 'results', query: buildResultQuery(resultId) }"
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
