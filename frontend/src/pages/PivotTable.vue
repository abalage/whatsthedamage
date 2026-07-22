<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { fetchResults } from '../js/api.js';
import { useFeedbackStore } from '../stores/feedback.js';
import { useGettext } from 'vue3-gettext';
import { usePivotStore } from '../stores/pivot.js';
import { useCategoriesStore } from '../stores/categories.js';
import type { Account } from '../types/api.js';
import type { BreadcrumbItem } from '../composables/useDrilldownData.js';
import BarChart from '../components/charts/BarChart.vue';
import PieChart from '../components/charts/PieChart.vue';
import PivotCategorySelector from '../components/PivotCategorySelector.vue';
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import BreadcrumbNavigation from '../components/layout/BreadcrumbNavigation.vue'
import LoadingState from '../components/layout/LoadingState.vue'
import ErrorState from '../components/layout/ErrorState.vue'

// VueDataTable component
import VueDataTable from '../components/data/VueDataTable.vue';
import type { Column, AggregateRowConfig } from '../components/data/VueDataTable.vue';
import { formatMonthYear } from '../js/dateUtils.js';

const { $gettext } = useGettext();
const feedback = useFeedbackStore();
const route = useRoute();
const pivotStore = usePivotStore();
const categoriesStore = useCategoriesStore();

const resultId = computed(() => route.params.resultId as string);
const isLoading = ref(true);
const error = ref<string | null>(null);

// Breadcrumb items
const breadcrumbItems = computed<BreadcrumbItem[]>(() => [
  { name: $gettext('Home'), to: '/' },
  { name: $gettext('Categories'), to: { name: 'results', query: { resultId: resultId.value } } },
  { name: $gettext('Pivot Table'), active: true }
]);

// Constants
const ZERO = 0;

const loadData = async () => {
  if (!resultId.value) {
    error.value = 'Missing result ID';
    isLoading.value = false;
    return;
  }

  try {
    const response = await fetchResults(resultId.value);
    await categoriesStore.loadCategories();
    await categoriesStore.loadCostOfLivingCategories();
    pivotStore.setResultsData(response);
    pivotStore.loadSettings();

    // If no account is selected, select the first one
    if (!selectedAccountId.value && response.accounts.length > ZERO) {
      pivotStore.setSelectedAccountId(response.accounts[ZERO].id);
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
    label: formatMonthYear(month.month_timestamp),
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
      month: formatMonthYear(month.month_timestamp),
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
          <ButtonComponent
            :text="$gettext('Back to Categories')"
            :to="{ name: 'results', query: { resultId: resultId } }"
            variant="secondary"
            class="mt-3 mb-3"
          />
        </template>
      </PageHeader>

      <!-- Account Selector -->
      <div v-if="accounts.length > 1">
        <CardComponent :title="$gettext('Select Account')" class="mb-4" width="auto">
          <label for="selectedAccountId" class="form-label">{{ $gettext('Account') }}</label>
          <select id="selectedAccountId" v-model="selectedAccountId" class="form-select">
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.formatted_id }} ({{ account.currency }})
            </option>
          </select>
        </CardComponent>
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
        <CardComponent :title="$gettext('Summary')" class="mb-4" width="auto">
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
        </CardComponent>
      </div>

      <!-- Bar Chart -->
      <div v-if="pivotData && selectedCategories.length > 0" class="mb-4">
        <CardComponent :title="$gettext('Monthly breakdown of selected categories')" class="mb-4" width="auto">
          <div class="form-check form-switch mb-0">
            <input id="showTrendline" v-model="pivotStore.showTrendline" class="form-check-input" type="checkbox" />
            <label class="form-check-label" for="showTrendline">{{ $gettext('Show trendline') }}</label>
          </div>
        <div class="card-body">
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
        </CardComponent>
      </div>

      <!-- Pie Charts -->
      <div v-if="pivotData && selectedCategories.length > 0" class="mb-4">
        <CardComponent :title="$gettext('Category Breakdown by Month')" class="mb-4" width="auto">
          <p class="text-secondary small mb-3"><i class="bi bi-info-circle me-1"></i> {{ $gettext('Each pie chart shows the composition of your selected categories for that month') }}</p>
          <div class="row">
            <div v-for="month in safeMonths" :key="month.month_timestamp" class="col-md-6 col-lg-4 mb-4">
              <CardComponent :title="formatMonthYear(month.month_timestamp)" class="mb-4" width="auto">
                <PieChart :data="Object.entries(month.categories).filter(([id]) => selectedCategories.includes(id)).map(([id, d]) => ({ label: getCategoryDisplayName(id), value: d.amount, categoryId: id }))" :total="month.total" />
              </CardComponent>
            </div>
          </div>
        </CardComponent>
      </div>

      <!-- Data Table - VueDataTable component -->
      <div v-if="pivotData && selectedCategories.length > 0">
        <CardComponent :title="$gettext('Detailed Monthly Data')" class="mb-4" width="auto">
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
        </CardComponent>
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
