/**
 * Theme type definitions for What's the Damage
 * Semantic design tokens for consistent theming
 */

/**
 * Highlight colors for data visualization
 */
interface ThemeHighlightColors {
  outlier: string;
  pareto: string;
  excluded: string;
  multiple: string;
}

/**
 * Chart-specific colors
 */
interface ThemeChartColors {
  category: string[];
  pie: string[];
  trendline: string;
}

/**
 * Status/semantic colors for feedback states
 */
interface ThemeStatusColors {
  success: string;
  warning: string;
  danger: string;
  info: string;
  success15: string;
  warning15: string;
  danger15: string;
  info15: string;
}

/**
 * Border colors for different border uses
 */
interface ThemeBorderColors {
  primary: string;
  secondary: string;
  subtle: string;
}

/**
 * Text colors for different text contexts
 */
interface ThemeTextColors {
  primary: string;
  secondary: string;
  onPrimary: string;
  onDark: string;
  onLight: string;
  onLight05: string;
  onLight10: string;
}

/**
 * Surface/background colors for different UI surfaces
 */
interface ThemeSurfaceColors {
  primary: string;
  secondary: string;
  elevated: string;
  base: string;
  primary10: string;
}

/**
 * All theme colors organized by semantic purpose
 */
interface ThemeColors {
  surface: ThemeSurfaceColors;
  text: ThemeTextColors;
  border: ThemeBorderColors;
  status: ThemeStatusColors;
  chart: ThemeChartColors;
  highlight: ThemeHighlightColors;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
  colors: ThemeColors;
}


