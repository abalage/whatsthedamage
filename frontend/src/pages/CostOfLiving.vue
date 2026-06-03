<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { fetchResults } from '../js/api';
import { useFeedbackStore } from '../stores/feedback';
import { useGettext } from 'vue3-gettext';
import { useCostOfLivingStore } from '../stores/costOfLiving';
import type { AccountDataResponse } from '../types/api';
import BarChart from '../components/charts/BarChart.vue';
import PieChart from '../components/charts/PieChart.vue';
import CostOfLivingCategorySelector from '../components/CostOfLivingCategorySelector.vue';

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
    
    // Initialize DataTables after data is loaded
    await initDataTablesIfReady();
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load data';
    feedback.showError('Failed to load Cost of Living data: ' + error.value);
    isLoading.value = false;
  }
};

// Computed from store
const costOfLivingData = computed(() => costOfLivingStore.costOfLivingData);
const resultsData = computed(() => costOfLivingStore.resultsData);
const selectedAccountId = computed(() => costOfLivingStore.selectedAccountId);
const selectedCategories = computed(() => costOfLivingStore.selectedCategoryIds);
const availableCategories = computed(() => costOfLivingStore.availableCategoryNames);
const accounts = computed<AccountDataResponse[]>(() => resultsData.value?.accounts_data.accounts || []);

const selectAccount = (accountId: string) => costOfLivingStore.setSelectedAccountId(accountId);

const monthlyBreakdown = computed(() => {
  if (!costOfLivingData.value) return [];
  return costOfLivingData.value.months.map(month => ({
    label: month.month,
    value: month.total
  }));
});

const trendlineValue = computed(() => costOfLivingData.value?.mean ?? ZERO);

// Use gettext directly on category IDs - translations are already configured
const getCategoryDisplayName = (categoryId: string): string => $gettext(categoryId);

const getCategoryUrl = (categoryId: string) => ({
  name: 'category-months',
  params: { resultId: resultId.value, accountId: selectedAccountId.value, categoryId }
});



// Auto-save settings
watch(() => [costOfLivingStore.selectedCategoryIds, costOfLivingStore.showTrendline], () => {
  costOfLivingStore.saveSettings();
}, { deep: true });

// Initialize and reinitialize DataTables when data is ready
const initDataTablesIfReady = async () => {
  if (costOfLivingData.value && selectedCategories.value.length > ZERO) {
    await nextTick()
    
    // Set translation strings for DataTables export buttons
    const w = globalThis as unknown as Window
    w.exportCsvText = $gettext('Export CSV')
    w.exportExcelText = $gettext('Export Excel')
    
    // Initialize DataTables
    w.initMainPage()
  }
}

// Reinitialize DataTables when selected categories or account changes
watch(() => [selectedCategories.value, selectedAccountId.value, costOfLivingData.value], async () => {
  await initDataTablesIfReady()
}, { deep: true });

onMounted(() => loadData());
</script>

<template>
  <div class="container">
    <!-- Breadcrumb -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ $gettext('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results' }">{{ $gettext('Results') }}</router-link></li>
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
          <router-link :to="{ name: 'results' }" class="btn btn-secondary">
            <i class="bi bi-arrow-left me-1"></i> {{ $gettext('Back to Results') }}
          </router-link>
        </div>
      </div>

      <!-- Account Selector -->
      <div v-if="accounts.length > 1" class="card mb-4">
        <div class="card-header"><h5>{{ $gettext('Select Account') }}</h5></div>
        <div class="card-body">
          <select v-model="selectedAccountId" class="form-select" @change="selectAccount(selectedAccountId)">
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.name }} ({{ account.id }})
            </option>
          </select>
        </div>
      </div>

      <!-- Account Info -->
      <div v-if="costOfLivingData" class="card mb-4">
        <div class="card-header">
          <h3><i class="bi bi-bank me-2"></i> {{ costOfLivingData.accountName }}</h3>
          <p class="text-muted mb-0"><i class="bi bi-currency-exchange me-1"></i> {{ $gettext('Currency') }}: {{ costOfLivingData.currency }}</p>
        </div>
        <div class="card-body">
          <p class="lead"><i class="bi bi-pie-chart me-2"></i> {{ $gettext('Cost of Living represents the sum of your selected essential living expenses.') }}</p>
          <p class="text-muted"><i class="bi bi-sliders me-2"></i> {{ $gettext('Customize which categories are included below.') }}</p>
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

      <!-- Main Visualizations (only when data exists and categories selected) -->
      <template v-if="costOfLivingData && selectedCategories.length > 0">
        
        <!-- Summary -->
        <div class="card mb-4">
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
                  <strong>{{ costOfLivingData.months.length }}</strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
                  <span><i class="bi bi-graph-up me-2"></i> {{ $gettext('Average Monthly') }}:</span>
                  <strong>{{ trendlineValue }}</strong>
                </div>
                <div class="d-flex justify-content-between">
                  <span><i class="bi bi-wallet2 me-2"></i> {{ $gettext('Total') }}:</span>
                  <strong>{{ costOfLivingData.months.reduce((sum, m) => sum + Math.abs(m.total), 0) }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Bar Chart -->
        <div class="card mb-4">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4 class="mb-0"><i class="bi bi-bar-chart me-2"></i> {{ $gettext('Monthly Cost of Living') }}</h4>
            <div class="form-check form-switch mb-0">
              <input id="showTrendline" v-model="costOfLivingStore.showTrendline" class="form-check-input" type="checkbox" />
              <label class="form-check-label" for="showTrendline">{{ $gettext('Show trendline') }}</label>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-wrapper"><BarChart :data="monthlyBreakdown" :show-trendline="costOfLivingStore.showTrendline" :trendline-value="trendlineValue" :currency="costOfLivingData.currency" /></div>
          </div>
        </div>

        <!-- Pie Charts -->
        <div class="card mb-4">
          <div class="card-header">
            <h4 class="mb-0"><i class="bi bi-pie-chart me-2"></i> {{ $gettext('Category Breakdown by Month') }}</h4>
          </div>
          <div class="card-body">
            <p class="text-muted small mb-3"><i class="bi bi-info-circle me-1"></i> {{ $gettext('Each pie chart shows the composition of your selected categories for that month') }}</p>
            <div class="row">
              <div v-for="month in costOfLivingData.months" :key="month.month_timestamp" class="col-md-6 col-lg-4 mb-4">
                <div class="h-100">
                  <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center p-2">
                      <h6 class="mb-0">{{ month.month }}</h6>
                      <span class="badge bg-primary">{{ month.total }}</span>
                    </div>
                    <div class="card-body p-2">
                      <PieChart :data="Object.entries(month.categories).filter(([id]) => selectedCategories.includes(id)).map(([id, d]) => ({ label: getCategoryDisplayName(id), value: d.amount, categoryId: id }))" :total="month.total" :currency="costOfLivingData.currency" />
                    </div>
                    <div class="card-footer p-2">
                      <div class="d-flex flex-wrap gap-1">
                        <router-link v-for="catId in selectedCategories.slice(0, 3)" :key="catId" :to="getCategoryUrl(catId)" class="btn btn-sm btn-outline-primary" :title="$gettext('View details for') + ' ' + getCategoryDisplayName(catId)">
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

        <!-- Data Table -->
        <div class="card">
          <div class="card-header"><h4 class="mb-0"><i class="bi bi-table me-2"></i> {{ $gettext('Detailed Monthly Data') }}</h4></div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table :id="`datatable-${selectedAccountId}`" class="table table-bordered table-hover mb-0 small" data-datatable="true">
                <thead class="table-light">
                  <tr>
                    <th scope="col" class="text-nowrap" data-order="month">{{ $gettext('Month') }}</th>
                    <th scope="col" class="text-nowrap" data-order="total">{{ $gettext('Cost of Living') }}</th>
                    <th v-for="catId in selectedCategories" :key="catId" scope="col" class="text-nowrap" :data-order="catId">{{ getCategoryDisplayName(catId) }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="month in costOfLivingData.months" :key="month.month_timestamp">
                    <td>{{ month.month }}</td>
                    <td class="fw-bold text-end" :data-order="Math.abs(month.total)">{{ Math.abs(month.total) }} {{ costOfLivingData.currency }}</td>
                    <td v-for="catId in selectedCategories" :key="catId" class="text-end" :data-order="month.categories[catId] ? Math.abs(month.categories[catId].amount) : 0">
                      {{ month.categories[catId] ? Math.abs(month.categories[catId].amount) : '0.00' }}
                    </td>
                  </tr>
                </tbody>
                <tfoot class="table-light">
                  <tr>
                    <th scope="col">{{ $gettext('Average') }}</th>
                    <th scope="col" class="fw-bold text-end">{{ trendlineValue }} {{ costOfLivingData.currency }}</th>
                    <th v-for="catId in selectedCategories" :key="catId" scope="col" class="text-end">
                      {{ costOfLivingData.months.length > 0 ? Math.abs(costOfLivingData.months.reduce((sum, m) => sum + (m.categories[catId]?.amount || 0), 0) / costOfLivingData.months.length) : '0.00' }}
                    </th>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </template>

      <div v-if="!costOfLivingData && !isLoading" class="alert alert-info">
        <i class="bi bi-inbox me-2"></i> {{ $gettext('No data available') }}
      </div>
    </div>

    <div v-else class="alert alert-info">
      <i class="bi bi-inbox me-2"></i> {{ $gettext('No Cost of Living data available') }}
    </div>
  </div>
</template>
