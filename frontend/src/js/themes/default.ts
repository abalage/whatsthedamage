/**
 * Default theme for What's the Damage
 * Original green theme with Bootstrap colors
 */

import type { Theme } from './theme.types.js';

const defaultTheme: Theme = {
  id: 'default',
  name: 'Default',
  description: 'Original green theme with Bootstrap colors',
  colors: {
    surface: {
      primary: '#28a745',
      secondary: '#6c757d',
      elevated: '#f8f9fa',
      base: '#ffffff',
      primary10: 'rgba(40, 167, 69, 0.10)',
    },
    text: {
      primary: '#28a745',
      secondary: '#6c757d',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#212529',
      onLight05: 'rgba(33, 37, 41, 0.05)',
      onLight10: 'rgba(33, 37, 41, 0.10)',
    },
    border: {
      primary: '#28a745',
      secondary: '#6c757d',
      subtle: '#dee2e6',
    },
    status: {
      success: '#28a745',
      warning: '#ffc107',
      danger: '#dc3545',
      info: '#0d6efd',
      success15: 'rgba(40, 167, 69, 0.15)',
      warning15: 'rgba(255, 193, 7, 0.15)',
      danger15: 'rgba(220, 53, 69, 0.15)',
      info15: 'rgba(13, 110, 253, 0.15)',
    },
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
};

export default defaultTheme;
