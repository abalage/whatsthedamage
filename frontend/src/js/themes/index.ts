/**
 * Theme registry for What's the Damage
 * Central registry that imports and exports all available themes
 */

import type { Theme } from './theme.types.js';
import defaultTheme from './default.js';
import softPastelTheme from './soft-pastel.js';
import earthTonesTheme from './earth-tones.js';
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

// Re-export types
export type { Theme } from './theme.types.js';
