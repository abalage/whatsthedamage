/**
 * Theme configurations for What's the Damage
 * Defines all available color palettes for the application
 */

interface ThemeHighlightColors {
  outlier: string;
  pareto: string;
  excluded: string;
  multiple: string;
}

interface ThemeChartColors {
  category: string[];
  pie: string[];
  trendline: string;
}

interface ThemeColors {
  primary: string;
  secondary: string;
  success: string;
  headerBg: string;
  headerText: string;
  cardHeaderBg: string;
  cardBodyBg: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  chart: ThemeChartColors;
  highlight: ThemeHighlightColors;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
  colors: ThemeColors;
}

/**
 * All available themes for the application
 * Add new themes to this array to make them available in the dropdown
 */
export const THEMES: Theme[] = [
  {
    id: 'default',
    name: 'Default',
    description: 'Original green theme with Bootstrap colors',
    colors: {
      primary: '#28a745',
      secondary: '#6c757d',
      success: '#28a745',
      headerBg: '#28a745',
      headerText: '#ffffff',
      cardHeaderBg: '#28a745',
      cardBodyBg: '#f8f9fa',
      textPrimary: '#28a745',
      textSecondary: '#6c757d',
      border: '#dee2e6',
      chart: {
        category: [
          '#0d6efd', // Blue - primary
          '#6610f2', // Purple
          '#dc3545', // Red
          '#fd7e14', // Orange
          '#ffc107', // Yellow
          '#198754', // Green
          '#20c997', // Teal
          '#0dcaf0', // Cyan
          '#6f42c1', // Indigo
          '#d63384', // Pink
          '#212529', // Dark
          '#6c757d', // Gray
        ],
        pie: [
          '#0d6efd',
          '#6610f2',
          '#6f42c1',
          '#d63384',
          '#dc3545',
          '#fd7e14',
          '#ffc107',
          '#198754',
          '#20c997',
          '#0dcaf0',
          '#6c757d',
          '#17a2b8',
        ],
        trendline: '#dc3545',
      },
      highlight: {
        outlier: '#ffe6e6',
        pareto: '#e6ffe6',
        excluded: '#f0f0f0',
        multiple: '#ffff99',
      },
    },
  },
  {
    id: 'soft-pastel',
    name: 'Soft Pastel Finance',
    description: 'Professional, calming, trustworthy with sage greens and teals',
    colors: {
      primary: '#81B29A',
      secondary: '#61A5C2',
      success: '#5A8A72',
      headerBg: '#5A8A72',
      headerText: '#ffffff',
      cardHeaderBg: '#5A8A72',
      cardBodyBg: '#F8F9FA',
      textPrimary: '#81B29A',
      textSecondary: '#61A5C2',
      border: '#E0E0E0',
      chart: {
        category: [
          '#81B29A', // Sage Green
          '#61A5C2', // Muted Teal
          '#B8C5D1', // Light Slate
          '#A4CAB8', // Mint Green
          '#8FB3A3', // Seafoam
          '#6BA3BE', // Steel Blue
          '#B2C7D6', // Powder Blue
          '#C4DBCB', // Light Sage
          '#9FB1BC', // Pale Slate
          '#D4E0D8', // Very Light Sage
          '#7CA998', // Darker Sage
          '#A8C7D2', // Light Steel
        ],
        pie: [
          '#81B29A',
          '#61A5C2',
          '#B8C5D1',
          '#A4CAB8',
          '#8FB3A3',
          '#6BA3BE',
          '#B2C7D6',
          '#C4DBCB',
          '#9FB1BC',
          '#D4E0D8',
          '#7CA998',
          '#A8C7D2',
        ],
        trendline: '#6BA3BE',
      },
      highlight: {
        outlier: '#FFE0E0',
        pareto: '#E0FFE0',
        excluded: '#F5F5F5',
        multiple: '#FFFFCC',
      },
    },
  },
  {
    id: 'earth-tones',
    name: 'Gentle Earth Tones',
    description: 'Natural, organic, balanced with olive and taupe',
    colors: {
      primary: '#7BA05B',
      secondary: '#88A47C',
      success: '#6B8A5F',
      headerBg: '#6B8A5F',
      headerText: '#ffffff',
      cardHeaderBg: '#6B8A5F',
      cardBodyBg: '#F8F9FA',
      textPrimary: '#7BA05B',
      textSecondary: '#88A47C',
      border: '#D4C4A8',
      chart: {
        category: [
          '#7BA05B', // Olive Green
          '#88A47C', // Muted Green
          '#B48EAD', // Soft Purple
          '#A89984', // Taupe
          '#92B4A7', // Green-Gray
          '#C9B488', // Sand
          '#B8A898', // Light Taupe
          '#8C9B86', // Darker Sage
          '#D4C4A8', // Light Sand
          '#A49586', // Warm Taupe
          '#99A888', // Medium Sage
          '#C4A892', // Warm Beige
        ],
        pie: [
          '#7BA05B',
          '#88A47C',
          '#B48EAD',
          '#A89984',
          '#92B4A7',
          '#C9B488',
          '#B8A898',
          '#8C9B86',
          '#D4C4A8',
          '#A49586',
          '#99A888',
          '#C4A892',
        ],
        trendline: '#8C9B86',
      },
      highlight: {
        outlier: '#F5E6E8',
        pareto: '#E8F5E8',
        excluded: '#F5F5F0',
        multiple: '#FFF9E6',
      },
    },
  },
  {
    id: 'mint-sky',
    name: 'Modern Mint & Sky',
    description: 'Fresh, clean, contemporary with mint greens and sky blues',
    colors: {
      primary: '#4ECDC4',
      secondary: '#82CAFF',
      success: '#3AB7A8',
      headerBg: '#3AB7A8',
      headerText: '#ffffff',
      cardHeaderBg: '#3AB7A8',
      cardBodyBg: '#F8F9FA',
      textPrimary: '#4ECDC4',
      textSecondary: '#82CAFF',
      border: '#D4F0F5',
      chart: {
        category: [
          '#4ECDC4', // Mint Teal
          '#82CAFF', // Light Sky Blue
          '#B4E1DC', // Very Light Mint
          '#6BCBC2', // Medium Mint
          '#95D7E0', // Light Cyan
          '#C4E5F0', // Pale Sky
          '#7FE0D1', // Bright Mint
          '#A8D8EA', // Soft Sky
          '#D4F0F5', // Very Pale Blue
          '#88D8C8', // Medium Mint
          '#5FD4D0', // Bright Cyan
          '#B8E8F0', // Very Pale Cyan
        ],
        pie: [
          '#4ECDC4',
          '#82CAFF',
          '#B4E1DC',
          '#6BCBC2',
          '#95D7E0',
          '#C4E5F0',
          '#7FE0D1',
          '#A8D8EA',
          '#D4F0F5',
          '#88D8C8',
          '#5FD4D0',
          '#B8E8F0',
        ],
        trendline: '#6BCBC2',
      },
      highlight: {
        outlier: '#FFE0E6',
        pareto: '#E0FFF0',
        excluded: '#F0F8FF',
        multiple: '#FFF0E6',
      },
    },
  },
  {
    id: 'corporate',
    name: 'Corporate Finance',
    description: 'Professional, banking, trustworthy with navy and forest green',
    colors: {
      primary: '#2C5F7A',
      secondary: '#4A7C59',
      success: '#1F4E6D',
      headerBg: '#1F4E6D',
      headerText: '#ffffff',
      cardHeaderBg: '#1F4E6D',
      cardBodyBg: '#F8F9FA',
      textPrimary: '#2C5F7A',
      textSecondary: '#6B8CAE',
      border: '#9BB8C8',
      chart: {
        category: [
          '#2C5F7A', // Deep Navy
          '#4A7C59', // Forest Green
          '#6B8CAE', // Steel Blue
          '#3A6B7B', // Dark Teal
          '#5C896B', // Sage Green
          '#7B9AA8', // Muted Blue
          '#4A7462', // Dark Sage
          '#8BA8B8', // Pale Steel
          '#5A8270', // Medium Sage
          '#9BB8C8', // Light Steel
          '#2A5871', // Darker Navy
          '#6C9CAF', // Medium Steel
        ],
        pie: [
          '#2C5F7A',
          '#4A7C59',
          '#6B8CAE',
          '#3A6B7B',
          '#5C896B',
          '#7B9AA8',
          '#4A7462',
          '#8BA8B8',
          '#5A8270',
          '#9BB8C8',
          '#2A5871',
          '#6C9CAF',
        ],
        trendline: '#7B9AA8',
      },
      highlight: {
        outlier: '#F0D0D0',
        pareto: '#D0F0D0',
        excluded: '#F5F5F5',
        multiple: '#FFFFD0',
      },
    },
  },
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
function getAllThemeIds(): string[] {
  return THEMES.map((t) => t.id);
}
