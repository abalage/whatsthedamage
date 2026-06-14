/**
 * Pinia store for Cost of Living settings and calculations
 *
 * This store manages:
 * - Results data from backend
 * - User-selected categories for Cost of Living
 * - Chart display preferences
 * - Calculated Cost of Living data
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ResultsApiResponse, AggregatedRow } from '../types/api.js';
import type { CostOfLivingSettings } from '../types/costOfLiving.js';
import { useCategoriesStore } from './categories.js';

// Constants
const ZERO = 0;
const ONE = 1;
const NEGATIVE_ONE = -1;

export const useCostOfLivingStore = defineStore('costOfLiving', () => {
  const categoriesStore = useCategoriesStore();

  // Results data from backend (via fetchResults)
  const resultsData = ref<ResultsApiResponse | null>(null);

  // Selected account ID (for multi-account support)
  const selectedAccountId = ref<string>('');

  // Default cost of living categories from the categories store
  const defaultCostOfLivingCategoryIds = computed(() => categoriesStore.costOfLivingCategories);

  // User-selected categories for Cost of Living
  const selectedCategoryIds = ref<string[]>([...defaultCostOfLivingCategoryIds.value]);

  // Chart display settings
  const showTrendline = ref<boolean>(true);

  // Computed: Get all available category names from results data
  const availableCategoryNames = computed<string[]>(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];

    const account = resultsData.value.accounts_data.accounts.find(
      (a) => a.id === selectedAccountId.value
    );

    if (!account) return [];

    const categories: Set<string> = new Set();
    for (const row of account.dt_response.data) {
      if (!row.is_calculated) {
        categories.add(row.category_id);
      }
    }
    return Array.from(categories).sort();
  });

  // Computed: Get all months for selected account
  const months = computed<{ display: string; timestamp: number }[]>(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];

    const account = resultsData.value.accounts_data.accounts.find(
      (a) => a.id === selectedAccountId.value
    );

    if (!account) return [];

    // Extract unique months from account data
    const monthMap = new Map<number, { display: string; timestamp: number }>();
    for (const row of account.dt_response.data) {
      monthMap.set(row.date.timestamp, {
        display: row.date.display,
        timestamp: row.date.timestamp
      });
    }

    // Sort by timestamp descending (most recent first)
    return Array.from(monthMap.values())
      .sort((a, b) => b.timestamp - a.timestamp);
  });

  // Computed: Calculate Cost of Living data from selected categories
  const costOfLivingData = computed<{
    months: Array<{
      month: string;
      month_timestamp: number;
      total: number;
      categories: Record<string, { amount: number; display: string }>;
    }>;
    mean: number;
    currency: string;
    accountName: string;
  } | null>(() => {
    if (!resultsData.value || !selectedAccountId.value) return null;

    const account = resultsData.value.accounts_data.accounts.find(
      (a) => a.id === selectedAccountId.value
    ) as { id: string; name: string; dt_response: { data: AggregatedRow[]; currency: string } } | undefined;

    if (!account || account.dt_response.data.length === ZERO) return null;

    // Create data for each month
    const monthsData = months.value.map(month => {
      let total = ZERO;
      const categories: Record<string, { amount: number; display: string }> = {};

      // Find all rows for this month
      for (const row of account.dt_response.data) {
        if (row.date.timestamp === month.timestamp && !row.is_calculated) {
          const amount = typeof row.total.raw === 'number'
            ? row.total.raw
            : Number.parseFloat(row.total.raw as string);

          // If this category is in our selection, add to total
          if (selectedCategoryIds.value.includes(row.category_id)) {
            total += amount;
          }

          // Always store category data for breakdown
          categories[row.category_id] = {
            amount,
            display: row.total.display
          };
        }
      }

      return {
        month: month.display,
        month_timestamp: month.timestamp,
        total,
        categories
      };
    });

    // Calculate mean (use absolute values)
    const totals = monthsData.map(m => Math.abs(m.total));
    const mean = totals.length > ZERO
      ? totals.reduce((a, b) => a + b, ZERO) / totals.length
      : ZERO;

    // Get currency from account's dt_response
    const currency = account.dt_response.currency ?? '';

    return {
      months: monthsData,
      mean,
      currency,
      accountName: account.name
    };
  });

  // ========== Actions ==========

  const setResultsData = (data: ResultsApiResponse): void => {
    resultsData.value = data;
    // Select first account by default
    if (data.accounts_data.accounts.length > ZERO) {
      selectedAccountId.value = data.accounts_data.accounts[ZERO].id;
    }
  };

  const setSelectedAccountId = (accountId: string): void => {
    selectedAccountId.value = accountId;
  };

  const toggleCategory = (categoryId: string): void => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > NEGATIVE_ONE) {
      selectedCategoryIds.value.splice(index, ONE);
    } else {
      selectedCategoryIds.value.push(categoryId);
    }
  };

  const addCategory = (categoryId: string): void => {
    if (!selectedCategoryIds.value.includes(categoryId)) {
      selectedCategoryIds.value.push(categoryId);
    }
  };

  const removeCategory = (categoryId: string): void => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > NEGATIVE_ONE) {
      selectedCategoryIds.value.splice(index, ONE);
    }
  };

  const setSelectedCategories = (categories: string[]): void => {
    selectedCategoryIds.value = [...categories];
  };

  const setShowTrendline = (show: boolean): void => {
    showTrendline.value = show;
  };

  const selectAll = (): void => {
    selectedCategoryIds.value = [...availableCategoryNames.value];
  };

  const clearAll = (): void => {
    selectedCategoryIds.value = [];
  };

  const resetToDefaults = (): void => {
    selectedCategoryIds.value = [...defaultCostOfLivingCategoryIds.value];
  };

  // ========== Persistence ==========

  const STORAGE_KEY = 'costOfLivingSettings';

  const saveSettings = (): void => {
    const settings: CostOfLivingSettings = {
      selectedCategoryIds: selectedCategoryIds.value,
      showTrendline: showTrendline.value,
      showDataLabels: true  // Currently not used but kept for future
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  };

  const loadSettings = (): void => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const settings: CostOfLivingSettings = JSON.parse(saved);
        selectedCategoryIds.value = settings.selectedCategoryIds ?? [...defaultCostOfLivingCategoryIds.value];
        showTrendline.value = settings.showTrendline ?? true;
      } catch {
        // Failed to load Cost of Living settings - silently ignore
      }
    }
  };

  return {
    // State
    resultsData,
    selectedAccountId,
    selectedCategoryIds,
    showTrendline,

    // Computed
    availableCategoryNames,
    months,
    costOfLivingData,
    defaultCostOfLivingCategoryIds,

    // Actions
    setResultsData,
    setSelectedAccountId,
    toggleCategory,
    addCategory,
    removeCategory,
    setSelectedCategories,
    setShowTrendline,
    selectAll,
    clearAll,
    resetToDefaults,

    // Persistence
    saveSettings,
    loadSettings
  };
});
