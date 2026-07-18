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
} from '../js/themes.ts';

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

    // Define all CSS variables to apply
    const cssVars: Record<string, string> = {
      '--primary-color': colors.primary,
      '--secondary-color': colors.secondary,
      '--success-color': colors.success,
      '--header-bg': colors.headerBg,
      '--header-text': colors.headerText,
      '--card-header-bg': colors.cardHeaderBg,
      '--card-body-bg': colors.cardBodyBg,
      '--text-primary': colors.textPrimary,
      '--text-secondary': colors.textSecondary,
      '--border-color': colors.border,
      '--highlight-outlier': colors.highlight.outlier,
      '--highlight-pareto': colors.highlight.pareto,
      '--highlight-excluded': colors.highlight.excluded,
      '--highlight-multiple': colors.highlight.multiple,
    };

    // Apply each CSS variable
    Object.entries(cssVars).forEach(([key, value]) => {
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
