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
import { DEFAULT_COST_OF_LIVING_CATEGORY_IDS, type CostOfLivingSettings } from '../types/costOfLiving';
import type { ResultsApiResponse } from '../types/api';

export const useCostOfLivingStore = defineStore('costOfLiving', () => {
  // Results data from backend (via fetchResults)
  const resultsData = ref<ResultsApiResponse | null>(null);
  
  // Selected account ID (for multi-account support)
  const selectedAccountId = ref<string>('');
  
  // User-selected categories for Cost of Living
  const selectedCategoryIds = ref<string[]>([...DEFAULT_COST_OF_LIVING_CATEGORY_IDS]);
  
  // Chart display settings
  const showTrendline = ref<boolean>(true);
  
  // Computed: Get all available category names from results data
  const availableCategoryNames = computed(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];
    
    const account = resultsData.value.accounts_data.accounts.find(
      a => a.id === selectedAccountId.value
    );
    
    if (!account) return [];
    
    const categories: Set<string> = new Set();
    for (const row of account.dt_response.data) {
      if (!row.is_calculated) {
        categories.add(row.category);
      }
    }
    return Array.from(categories).sort();
  });
  
  // Computed: Get all months for selected account
  const months = computed(() => {
    if (!resultsData.value || !selectedAccountId.value) return [];
    
    const account = resultsData.value.accounts_data.accounts.find(
      a => a.id === selectedAccountId.value
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
  const costOfLivingData = computed(() => {
    if (!resultsData.value || !selectedAccountId.value) return null;
    
    const account = resultsData.value.accounts_data.accounts.find(
      a => a.id === selectedAccountId.value
    );
    
    if (!account || account.dt_response.data.length === 0) return null;
    
    // Create data for each month
    const monthsData = months.value.map(month => {
      let total = 0;
      const categories: Record<string, { amount: number; display: string }> = {};
      
      // Find all rows for this month
      for (const row of account.dt_response.data) {
        if (row.date.timestamp === month.timestamp && !row.is_calculated) {
          const amount = typeof row.total.raw === 'number'
            ? row.total.raw
            : Number.parseFloat(row.total.raw as string);
          
          // If this category is in our selection, add to total
          if (selectedCategoryIds.value.includes(row.category)) {
            total += amount;
          }
          
          // Always store category data for breakdown
          categories[row.category] = {
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
    
    // Get currency from account's dt_response
    const currency = account.dt_response.currency || '';
    
    return {
      months: monthsData,
      mean,
      currency,
      accountName: account.name
    };
  });
  
  // ========== Actions ==========
  
  const setResultsData = (data: ResultsApiResponse) => {
    resultsData.value = data;
    // Select first account by default
    if (data.accounts_data.accounts.length > 0) {
      selectedAccountId.value = data.accounts_data.accounts[0].id;
    }
  };
  
  const setSelectedAccountId = (accountId: string) => {
    selectedAccountId.value = accountId;
  };
  
  const toggleCategory = (categoryId: string) => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > -1) {
      selectedCategoryIds.value.splice(index, 1);
    } else {
      selectedCategoryIds.value.push(categoryId);
    }
  };
  
  const addCategory = (categoryId: string) => {
    if (!selectedCategoryIds.value.includes(categoryId)) {
      selectedCategoryIds.value.push(categoryId);
    }
  };
  
  const removeCategory = (categoryId: string) => {
    const index = selectedCategoryIds.value.indexOf(categoryId);
    if (index > -1) {
      selectedCategoryIds.value.splice(index, 1);
    }
  };
  
  const setSelectedCategories = (categories: string[]) => {
    selectedCategoryIds.value = [...categories];
  };
  
  const setShowTrendline = (show: boolean) => {
    showTrendline.value = show;
  };
  
  const selectAll = () => {
    selectedCategoryIds.value = [...availableCategoryNames.value];
  };
  
  const clearAll = () => {
    selectedCategoryIds.value = [];
  };
  
  const resetToDefaults = () => {
    selectedCategoryIds.value = [...DEFAULT_COST_OF_LIVING_CATEGORY_IDS];
  };
  
  // ========== Persistence ==========
  
  const STORAGE_KEY = 'costOfLivingSettings';
  
  const saveSettings = () => {
    const settings: CostOfLivingSettings = {
      selectedCategoryIds: selectedCategoryIds.value,
      showTrendline: showTrendline.value,
      showDataLabels: true  // Currently not used but kept for future
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  };
  
  const loadSettings = () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const settings: CostOfLivingSettings = JSON.parse(saved);
        selectedCategoryIds.value = settings.selectedCategoryIds || [...DEFAULT_COST_OF_LIVING_CATEGORY_IDS];
        showTrendline.value = settings.showTrendline ?? true;
      } catch {
        console.warn('Failed to load Cost of Living settings');
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