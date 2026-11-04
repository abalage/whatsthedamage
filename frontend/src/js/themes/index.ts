/**
 * Theme registry for What's the Damage
 * Central registry that imports and exports all available themes
 */

import type { Theme } from './theme.types';
import balticBlueTheme from './baltic-blue';

/**
 * The single application theme - do not add new themes
 */
export const THEMES: Theme[] = [
  balticBlueTheme
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
export type { Theme } from './theme.types';
