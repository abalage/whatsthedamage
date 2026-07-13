/**
 * Types for Pivot table feature
 */

// Pivot table user settings (stored in localStorage)
export interface PivotSettings {
  selectedCategoryIds: string[];
  showTrendline: boolean;
  showDataLabels: boolean;
}
