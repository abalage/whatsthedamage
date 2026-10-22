/**
 * Pinia store for Pivot settings and calculations
 *
 * This store manages:
 * - Results data from backend
 * - User-selected categories for Pivot (persisted)
 * - Chart display preferences (persisted)
 * - Calculated Pivot data
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ResultsApiResponse, Account } from '../types/api';
import { useCategoriesStore } from './categories';
import { usePersistentRef } from '../composables/usePersistentRef';

const SELECTED_CATEGORIES_KEY = 'pivotSelectedCategoryIds';
const SHOW_TRENDLINE_KEY = 'pivotShowTrendline';

export const usePivotStore = defineStore('pivot', () => {
  const categoriesStore = useCategoriesStore();

  // Results data from backend (via fetchAllTransactions + transform)
  const resultsData = ref<ResultsApiResponse | null>(null);

  // Selected account ID (for multi-account support)
  const selectedAccountId = ref<string>('');

  // Default Pivot categories from the categories store
  const defaultCostOfLivingCategoryIds = computed(() => categoriesStore.costOfLivingCategories);

  // User-selected categories for Pivot (persisted)
  const selectedCategoryIds = usePersistentRef<string[]>(
    SELECTED_CATEGORIES_KEY,
    [...defaultCostOfLivingCategoryIds.value],
    (value): value is string[] =>
      Array.isArray(value) && value.every(v => typeof v === 'string')
  );

  // Chart display settings (persisted)
  const showTrendline = usePersistentRef<boolean>(
    SHOW_TRENDLINE_KEY,
    true,
    (value): value is boolean => typeof value === 'boolean'
  );

  // Computed: Get all available category names from results data
  const availableCategoryNames = computed<string[]>(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];

    const account = resultsData.value.accounts.find(
      (a) => a.id === selectedAccountId.value
    );

    if (!account?.data) return [];

    const categories: Set<string> = new Set();
    for (const row of account.data) {
      if (!row.is_calculated) {
        categories.add(row.category_id);
      }
    }
    return Array.from(categories).sort();
  });

  // Computed: Get all months for selected account
  const months = computed<{ display: string; timestamp: number }[]>(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];

    const account = resultsData.value.accounts.find(
      (a) => a.id === selectedAccountId.value
    );

    if (!account?.data) return [];

    // Extract unique months from account data
    // row.date is now an ISO 8601 string (YYYY-MM-DD)
    const monthMap = new Map<string, { display: string; timestamp: number }>();
    for (const row of account.data) {
      const dateStr = row.date as string;
      // Extract YYYY-MM from ISO date string
      const monthKey = dateStr?.substring(0, 7) || 'unknown';
      // Convert to timestamp for sorting
      const timestamp = dateStr ? Math.floor(new Date(dateStr).getTime() / 1000) : 0;

      if (!monthMap.has(monthKey)) {
        monthMap.set(monthKey, {
          display: monthKey,  // Use YYYY-MM as display
          timestamp: timestamp
        });
      }
    }

    // Sort by timestamp descending (most recent first)
    return Array.from(monthMap.values())
      .sort((a, b) => b.timestamp - a.timestamp);
  });

  // Computed: Calculate Pivot data from selected categories
  const pivotData = computed<{
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

    const account = resultsData.value.accounts.find(
      (a) => a.id === selectedAccountId.value
    ) as Account | undefined;

    const accountData = account?.data;
    if (!accountData?.length || !account) return null;

    // Create data for each month
    const monthsData = months.value.map(month => {
      let total = 0;
      const categories: Record<string, { amount: number; display: string }> = {};

      // Find all rows for this month
      for (const row of accountData) {
        // row.date is now an ISO 8601 string (YYYY-MM-DD)
        const rowTimestamp = row.date ? Math.floor(new Date(row.date as string).getTime() / 1000) : 0;

        if (rowTimestamp === month.timestamp && !row.is_calculated) {
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
    const mean = totals.length > 0
      ? totals.reduce((a, b) => a + b, 0) / totals.length
      : 0;

    return {
      months: monthsData,
      mean,
      currency: account.currency ?? '',
      accountName: account.name
    };
  });

  // ========== Actions ==========

  const setResultsData = (data: ResultsApiResponse): void => {
    resultsData.value = data;
    // Select first account by default
    if (data.accounts.length > 0) {
      selectedAccountId.value = data.accounts[0].id;
    }
  };

  const setSelectedAccountId = (accountId: string): void => {
    selectedAccountId.value = accountId;
  };

  const toggleCategory = (categoryId: string): void => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > -1) {
      selectedCategoryIds.value = [
        ...selectedCategoryIds.value.slice(0, index),
        ...selectedCategoryIds.value.slice(index + 1)
      ];
    } else {
      selectedCategoryIds.value = [...selectedCategoryIds.value, categoryId];
    }
  };

  const addCategory = (categoryId: string): void => {
    if (!selectedCategoryIds.value.includes(categoryId)) {
      selectedCategoryIds.value = [...selectedCategoryIds.value, categoryId];
    }
  };

  const removeCategory = (categoryId: string): void => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > -1) {
      selectedCategoryIds.value = [
        ...selectedCategoryIds.value.slice(0, index),
        ...selectedCategoryIds.value.slice(index + 1)
      ];
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

  return {
    // State
    resultsData,
    selectedAccountId,
    selectedCategoryIds,
    showTrendline,

    // Computed
    availableCategoryNames,
    months,
    pivotData,
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
    resetToDefaults
  };
});
