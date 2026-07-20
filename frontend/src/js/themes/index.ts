/**
 * Theme registry for What's the Damage
 * Central registry that imports and exports all available themes
 */

import type { Theme } from './theme.types.js';
import defaultTheme from './default.js';
import softPastelTheme from './soft-pastel.js';
import earthTonesTheme from './earth-tones.js';
import mintSkyTheme from './mint-sky.js';
import corporateTheme from './corporate.js';
import pickerTheme from './picker.js';

/**
 * All available themes for the application
 * Add new themes by importing them above and adding to this array
 */
export const THEMES: Theme[] = [
  defaultTheme,
  softPastelTheme,
  earthTonesTheme,
  mintSkyTheme,
  corporateTheme,
  pickerTheme,
];

/**
 * Get theme by ID
 */
export function getThemeById(id: string): Theme | undefined {
  return THEMES.find((t) => t.id === id);
}

/**
 * Get the default theme (first in array)
 */
export function getDefaultTheme(): Theme {
  return THEMES[0];
}

/**
 * Get all theme IDs
 */
export function getAllThemeIds(): string[] {
  return THEMES.map((t) => t.id);
}

// Re-export types
export type { Theme, ThemeColors, ThemeChartColors, ThemeHighlightColors } from './theme.types.js';
