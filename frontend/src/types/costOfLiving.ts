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
// These are category IDs (lowercase with underscores), not display names
export const DEFAULT_COST_OF_LIVING_CATEGORY_IDS = [
  'grocery',
  'loan',
  'transportation',
  'utility',
  'payment',
  'fee',
  'health'
] as const;
