<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { fetchResults } from '../js/api.js';
import { useFeedbackStore } from '../stores/feedback.js';
import { useGettext } from 'vue3-gettext';
import { useCostOfLivingStore } from '../stores/costOfLiving.js';
import type { AccountDataResponse } from '../types/api.js';
import BarChart from '../components/charts/BarChart.vue';
import PieChart from '../components/charts/PieChart.vue';
import CostOfLivingCategorySelector from '../components/CostOfLivingCategorySelector.vue';

// DataTable Vue3 component imports
import DataTable from 'datatables.net-vue3';
import DataTablesLib from 'datatables.net-bs5';
import 'datatables.net-buttons-bs5';
import 'datatables.net-fixedheader-bs5';
import 'datatables.net-buttons/js/buttons.html5';
import type { Config } from 'datatables.net';

// DataTables column type - ConfigColumns is not exported from datatables.net
interface DataTableColumn {
  title: string;
  data: string | number;
  className?: string;
  orderable?: boolean;
  render?: (data: any, type: string) => any;
}

// Register DataTables library with the Vue component
DataTable.use(DataTablesLib);

const { $gettext } = useGettext();
const feedback = useFeedbackStore();
const route = useRoute();
const costOfLivingStore = useCostOfLivingStore();

const resultId = computed(() => route.params.resultId as string);
const isLoading = ref(true);
const error = ref<string | null>(null);

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
    costOfLivingStore.setResultsData(response);
    costOfLivingStore.loadSettings();
    
    // If no account is selected, select the first one
    if (!selectedAccountId.value && response.accounts_data.accounts.length > ZERO) {
      costOfLivingStore.setSelectedAccountId(response.accounts_data.accounts[ZERO].id);
    }
    
    isLoading.value = false;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load data';
    feedback.showError('Failed to load Cost of Living data: ' + error.value);
    isLoading.value = false;
  }
};

// Computed from store
const costOfLivingData = computed(() => costOfLivingStore.costOfLivingData);
const resultsData = computed(() => costOfLivingStore.resultsData);
const selectedAccountId = computed({
  get: () => costOfLivingStore.selectedAccountId,
  set: (value: string) => costOfLivingStore.setSelectedAccountId(value)
});
const selectedCategories = computed(() => costOfLivingStore.selectedCategoryIds);
const availableCategories = computed(() => costOfLivingStore.availableCategoryNames);
const accounts = computed<AccountDataResponse[]>(() => resultsData.value?.accounts_data.accounts || []);

const monthlyBreakdown = computed(() => {
  if (!costOfLivingData.value) return [];
  return costOfLivingData.value.months.map(month => ({
    label: month.month,
    value: month.total,
    timestamp: month.month_timestamp
  }));
});

const trendlineValue = computed(() => costOfLivingData.value?.mean ?? ZERO);

// Safe access to months for DataTable footer calculations
const safeMonths = computed(() => costOfLivingData.value?.months || []);

// Use gettext directly on category IDs - translations are already configured
const getCategoryDisplayName = (categoryId: string): string => $gettext(categoryId);

// NEW: Table column definitions for DataTable
const tableColumns = computed<DataTableColumn[]>(() => {
  const columns: DataTableColumn[] = [
    {
      title: $gettext('Month'),
      data: 'month',
      className: 'text-nowrap',
      orderable: true
    },
    {
      title: $gettext('Cost of Living'),
      data: 'total',
      className: 'text-nowrap text-end',
      orderable: true,
      render: (data: number, type: string) => {
        if (type === 'display') {
          return `${Math.abs(data)}`;
        }
        return Math.abs(data);
      }
    }
  ];

  // Add columns for each selected category
  selectedCategories.value.forEach(catId => {
    columns.push({
      title: getCategoryDisplayName(catId),
      data: catId,
      className: 'text-nowrap text-end',
      orderable: true,
      render: (data: { amount: number } | null, type: string) => {
        const amount = data?.amount ?? ZERO;
        if (type === 'display') {
          return `${Math.abs(amount)}`;
        }
        return Math.abs(amount);
      }
    });
  });

  return columns;
});

// NEW: Table data for DataTable
const tableData = computed<Record<string, unknown>[]>(() => {
  if (!costOfLivingData.value) return [];

  return costOfLivingData.value.months.map(month => {
    const row: Record<string, unknown> = {
      month: month.month,
      total: month.total
    };

    // Add category data for each selected category
    selectedCategories.value.forEach(catId => {
      row[catId] = month.categories[catId] ?? { amount: ZERO };
    });

    return row;
  });
});

// NEW: Table options for DataTable
const tableOptions = computed<Config>(() => ({
  responsive: true,
  pageLength: 25,
  dom: '<"dt-buttons"B><"clear">frtip',
  buttons: [
    {
      extend: 'csvHtml5',
      text: $gettext('Export CSV'),
      className: 'btn'
    },
    {
      extend: 'excelHtml5',
      text: $gettext('Export Excel'),
      className: 'btn'
    }
  ],
  order: [[ZERO, 'desc']], // Sort by month descending by default
  language: {
    search: $gettext('Search') + ': ',
    lengthMenu: $gettext('Show _MENU_ entries'),
    info: $gettext('Showing _START_ to _END_ of _TOTAL_ entries'),
    infoEmpty: $gettext('Showing 0 to 0 of 0 entries'),
    infoFiltered: $gettext('(filtered from _MAX_ total entries)'),
    paginate: {
      first: $gettext('First'),
      last: $gettext('Last'),
      next: $gettext('Next'),
      previous: $gettext('Previous')
    }
  }
}));

// NEW: Helper function to calculate category average
const calculateCategoryAverage = (catId: string): string => {
  if (safeMonths.value.length === ZERO) return '0.00';
  const sum = safeMonths.value.reduce(
    (acc, m) => acc + Math.abs(m.categories[catId]?.amount || ZERO),
    ZERO
  );
  return (sum / safeMonths.value.length).toFixed(2);
};

const getCategoryUrl = (categoryId: string) => ({
  name: 'category-months',
  params: { resultId: resultId.value, accountId: selectedAccountId.value, categoryId }
});

// Auto-save settings
watch(() => [costOfLivingStore.selectedCategoryIds, costOfLivingStore.showTrendline], () => {
  costOfLivingStore.saveSettings();
}, { deep: true });

onMounted(() => loadData());
</script>

<template>
  <div class="container">
    <!-- Breadcrumb -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ $gettext('Categories') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ $gettext('Cost of Living') }}</li>
      </ol>
    </nav>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-primary">
        <span class="mt-2">{{ $gettext('Loading Cost of Living data') }}...</span>
      </output>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="resultsData">
      <!-- Header -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1><i class="bi bi-house-heart me-2"></i> {{ $gettext('Cost of Living Analysis') }}</h1>
        <div class="d-flex gap-2">
          <router-link :to="{ name: 'results', query: { resultId: resultId } }" class="btn btn-secondary">
            <i class="bi bi-arrow-left me-1"></i> {{ $gettext('Back to Categories') }}
          </router-link>
        </div>
      </div>

      <!-- Account Selector -->
      <div v-if="accounts.length > 1" class="card mb-4">
        <div class="card-header"><h5>{{ $gettext('Select Account') }}</h5></div>
        <div class="card-body">
          <select v-model="selectedAccountId" class="form-select">
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Category Selector -->
      <CostOfLivingCategorySelector v-if="availableCategories.length > 0" />
      
      <div v-else class="alert alert-warning">
        <i class="bi bi-exclamation-triangle-fill me-2"></i> {{ $gettext('No categories found in the data') }}
      </div>
      
      <div v-if="selectedCategories.length === 0 && availableCategories.length > 0" class="alert alert-info mb-4">
        <i class="bi bi-info-circle me-2"></i> {{ $gettext('Please select at least one category to see Cost of Living calculations') }}
      </div>

      <!-- Summary -->
      <div v-if="costOfLivingData && selectedCategories.length > 0" class="card mb-4">
        <div class="card-header"><h4><i class="bi bi-bar-chart-line me-2"></i> {{ $gettext('Summary') }}</h4></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <div class="d-flex justify-content-between mb-2">
                <span><i class="bi bi-tags me-2"></i> {{ $gettext('Selected Categories') }}:</span>
                <strong>{{ selectedCategories.length }}</strong>
              </div>
              <div class="selected-categories-list small text-muted">{{ selectedCategories.map(getCategoryDisplayName).join(', ') }}</div>
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

      <!-- Bar Chart -->
      <div v-if="costOfLivingData && selectedCategories.length > 0" class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h4 class="mb-0"><i class="bi bi-bar-chart me-2"></i> {{ $gettext('Monthly Cost of Living') }}</h4>
          <div class="form-check form-switch mb-0">
            <input id="showTrendline" v-model="costOfLivingStore.showTrendline" class="form-check-input" type="checkbox" />
            <label class="form-check-label" for="showTrendline">{{ $gettext('Show trendline') }}</label>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-wrapper"><BarChart :data="monthlyBreakdown" :show-trendline="costOfLivingStore.showTrendline"/></div>
        </div>
      </div>

      <!-- Pie Charts -->
      <div v-if="costOfLivingData && selectedCategories.length > 0" class="card mb-4">
        <div class="card-header">
          <h4 class="mb-0"><i class="bi bi-pie-chart me-2"></i> {{ $gettext('Category Breakdown by Month') }}</h4>
        </div>
        <div class="card-body">
          <p class="text-muted small mb-3"><i class="bi bi-info-circle me-1"></i> {{ $gettext('Each pie chart shows the composition of your selected categories for that month') }}</p>
          <div class="row">
            <div v-for="month in safeMonths" :key="month.month_timestamp" class="col-md-6 col-lg-4 mb-4">
              <div class="h-100">
                <div class="card h-100">
                  <div class="card-header d-flex justify-content-between align-items-center p-2">
                    <h6 class="mb-0">{{ month.month }}</h6>
                    <span class="badge bg-primary">{{ month.total }}</span>
                  </div>
                  <div class="card-body p-2">
                    <PieChart :data="Object.entries(month.categories).filter(([id]) => selectedCategories.includes(id)).map(([id, d]) => ({ label: getCategoryDisplayName(id), value: d.amount, categoryId: id }))" :total="month.total" />
                  </div>
                  <div class="card-footer p-2">
                    <div class="d-flex flex-wrap gap-1">
                      <router-link v-for="catId in selectedCategories.slice(0, 3)" :key="catId" :to="getCategoryUrl(catId)" class="btn btn-sm btn-outline-primary" :title="$gettext('Details') + ': ' + getCategoryDisplayName(catId)">
                        <i class="bi bi-box-arrow-up-right me-1"></i>{{ getCategoryDisplayName(catId).substring(0, 8) }}
                      </router-link>
                      <span v-if="selectedCategories.length > 3" class="small text-muted ms-2">+{{ selectedCategories.length - 3 }} {{ $gettext('more') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Table - Vue3-native DataTable component -->
      <div v-if="costOfLivingData && selectedCategories.length > 0" class="card">
        <div class="card-header"><h4 class="mb-0"><i class="bi bi-table me-2"></i> {{ $gettext('Detailed Monthly Data') }}</h4></div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <DataTable
              :key="`columns-${selectedCategories.join(',')}-${costOfLivingData?.months.length}`"
              :columns="tableColumns"
              :data="tableData"
              :options="tableOptions"
              class="display table table-bordered table-hover mb-0 small"
            >
              <thead class="table-light">
                <tr>
                  <th
                    v-for="col in tableColumns"
                    :key="col.data ?? col.title"
                    :class="col.className"
                    scope="col"
                  >
                    {{ col.title }}
                  </th>
                </tr>
              </thead>
              <tfoot class="table-light">
                <tr>
                  <th scope="col">{{ $gettext('Average') }}</th>
                  <th scope="col" class="fw-bold text-end">{{ trendlineValue }}</th>
                  <th v-for="catId in selectedCategories" :key="catId" scope="col" class="text-end">
                    {{ calculateCategoryAverage(catId) }}
                  </th>
                </tr>
              </tfoot>
            </DataTable>
          </div>
        </div>
      </div>

      <div v-if="!costOfLivingData && !isLoading" class="alert alert-info">
        <i class="bi bi-inbox me-2"></i> {{ $gettext('No data available') }}
      </div>
    </div>

    <div v-else class="alert alert-info">
      <i class="bi bi-inbox me-2"></i> {{ $gettext('No Cost of Living data available') }}
    </div>
  </div>
</template>
