/**
 * Theme Store for What's the Damage
 * Manages the current color theme and applies it to the application
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  THEMES,
  getThemeById,
  getDefaultTheme,
  type Theme,
} from '../js/themes/index.js';

export type { Theme };

const STORAGE_KEY = 'wtb-theme-preference';

export const useThemeStore = defineStore('theme', () => {
  // State - current theme ID
  const currentThemeId = ref<string>('');

  // Getters

  /**
   * Get the current theme object
   */
  const currentTheme = computed((): Theme => {
    if (!currentThemeId.value) {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && getThemeById(saved)) {
        currentThemeId.value = saved;
        return getThemeById(saved)!;
      }
      currentThemeId.value = getDefaultTheme().id;
      return getDefaultTheme();
    }
    const theme = getThemeById(currentThemeId.value);
    return theme ?? getDefaultTheme();
  });

  /**
   * Get all available themes
   */
  const allThemes = computed((): Theme[] => THEMES);

  // Actions

  /**
   * Set the current theme by ID
   * Persists to localStorage and applies the theme
   */
  function setTheme(themeId: string): void {
    const theme = getThemeById(themeId);
    if (theme) {
      currentThemeId.value = themeId;
      localStorage.setItem(STORAGE_KEY, themeId);
      applyTheme(theme);
    }
  }

  /**
   * Apply a theme to the document by setting CSS variables
   */
  function applyTheme(theme: Theme): void {
    const root = document.documentElement;
    const colors = theme.colors;

    // Semantic CSS variables (new structure)
    const semanticVars: Record<string, string> = {
      // Surface colors
      '--color-surface-primary': colors.surface.primary,
      '--color-surface-secondary': colors.surface.secondary,
      '--color-surface-elevated': colors.surface.elevated,
      '--color-surface-base': colors.surface.base,
      '--color-surface-primary-10': colors.surface.primary10,
      
      // Text colors
      '--color-text-primary': colors.text.primary,
      '--color-text-secondary': colors.text.secondary,
      '--color-text-on-primary': colors.text.onPrimary,
      '--color-text-on-dark': colors.text.onDark,
      '--color-text-on-light': colors.text.onLight,
      '--color-text-on-light-05': colors.text.onLight05,
      '--color-text-on-light-10': colors.text.onLight10,
      
      // Border colors
      '--color-border-primary': colors.border.primary,
      '--color-border-secondary': colors.border.secondary,
      '--color-border-subtle': colors.border.subtle,
      
      // Status colors
      '--color-status-success': colors.status.success,
      '--color-status-warning': colors.status.warning,
      '--color-status-danger': colors.status.danger,
      '--color-status-info': colors.status.info,
      '--color-status-success-15': colors.status.success15,
      '--color-status-warning-15': colors.status.warning15,
      '--color-status-danger-15': colors.status.danger15,
      '--color-status-info-15': colors.status.info15,
      
      // Highlight colors
      '--color-highlight-outlier': colors.highlight.outlier,
      '--color-highlight-pareto': colors.highlight.pareto,
      '--color-highlight-excluded': colors.highlight.excluded,
      '--color-highlight-multiple': colors.highlight.multiple,
    };

    // Legacy CSS variables (mapped from semantic structure for backward compatibility)
    const legacyVars: Record<string, string> = {
      '--primary-color': colors.surface.primary,
      '--secondary-color': colors.surface.secondary,
      '--success-color': colors.status.success,
      '--warning-color': colors.status.warning,
      '--danger-color': colors.status.danger,
      '--info-color': colors.status.info,
      '--light-color': colors.surface.elevated,
      '--dark-color': colors.text.onLight,
      '--header-bg': colors.surface.primary,
      '--header-text': colors.text.onPrimary,
      '--card-header-bg': colors.surface.primary,
      '--card-body-bg': colors.surface.elevated,
      '--text-primary': colors.text.primary,
      '--text-secondary': colors.text.secondary,
      '--border-color': colors.border.subtle,
      '--highlight-outlier': colors.highlight.outlier,
      '--highlight-pareto': colors.highlight.pareto,
      '--highlight-excluded': colors.highlight.excluded,
      '--highlight-multiple': colors.highlight.multiple,
    };

    // Apply all CSS variables
    Object.entries({ ...semanticVars, ...legacyVars }).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });

    // Apply chart colors as individual CSS variables
    colors.chart.category.forEach((color: string, index: number) => {
      root.style.setProperty(`--chart-color-${index + 1}`, color);
    });

    // Dispatch custom event for components that need to react to theme changes
    window.dispatchEvent(
      new CustomEvent('theme-changed', { detail: { theme } })
    );
  }

  /**
   * Initialize the theme store
   * Loads saved preference or defaults to the first theme
   */
  function initialize(): void {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && getThemeById(saved)) {
      currentThemeId.value = saved;
      applyTheme(getThemeById(saved)!);
    } else {
      // No saved preference, use default
      currentThemeId.value = getDefaultTheme().id;
      applyTheme(getDefaultTheme());
    }
  }

  /**
   * Reset to default theme
   */
  function resetToDefault(): void {
    localStorage.removeItem(STORAGE_KEY);
    setTheme(getDefaultTheme().id);
  }

  // Auto-initialize when store is created
  initialize();

  return {
    currentThemeId,
    currentTheme,
    allThemes,
    setTheme,
    applyTheme,
    initialize,
    resetToDefault,
  };
});
