/**
 * Statistical Analysis - Legacy DOM-based functionality removed
 * 
 * All statistical analysis is now handled via Vue3-native reactive components.
 * See Layout.vue for the current implementation using Pinia store.
 */

// This file is kept for backward compatibility but all DOM-based highlighting
// has been migrated to Vue3-native reactive highlighting via:
// - Pinia statisticalStore for state management
// - VueDataTable component with cellHighlightsByRowId prop
// - Cell-level _rowIds mapping for pivot tables

// No legacy DOM manipulation functions are exported anymore.
