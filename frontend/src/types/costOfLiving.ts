/**
 * Types for Cost of Living feature
 */

// Cost of Living user settings (stored in localStorage)
export interface CostOfLivingSettings {
  selectedCategoryIds: string[];
  showTrendline: boolean;
  showDataLabels: boolean;
}

// Default categories (MUST match backend config.py COST_OF_LIVING_CATEGORY_IDS)
export const DEFAULT_COST_OF_LIVING_CATEGORY_IDS = [
  'Grocery',
  'Loan',
  'Transportation',
  'Utility',
  'Payment',
  'Fee',
  'Health'
] as const;
