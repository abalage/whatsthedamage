/**
 * Types for Cost of Living feature
 */

// Cost of Living user settings (stored in localStorage)
export interface CostOfLivingSettings {
  selectedCategoryIds: string[];
  showTrendline: boolean;
  showDataLabels: boolean;
}
