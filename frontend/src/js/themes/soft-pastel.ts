/**
 * Soft Pastel Finance theme for What's the Damage
 * Professional, calming, trustworthy with sage greens and teals
 */

import type { Theme } from './theme.types.js';

const softPastelTheme: Theme = {
  id: 'soft-pastel',
  name: 'Soft Pastel Finance',
  description: 'Professional, calming, trustworthy with sage greens and teals',
  colors: {
    surface: {
      primary: '#5A8A72',
      secondary: '#81B29A',
      elevated: '#F8F9FA',
      base: '#FFFFFF',
      primary10: 'rgba(129, 178, 154, 0.10)',
    },
    text: {
      primary: '#151515',
      secondary: '#5e5e5e',
      onPrimary: '#FFFFFF',
      onDark: '#FFFFFF',
      onLight: '#3A4A52',
      onLight05: 'rgba(58, 74, 82, 0.05)',
      onLight10: 'rgba(58, 74, 82, 0.10)',
    },
    border: {
      primary: '#61A5C2',
      secondary: '#81B29A',
      subtle: '#E0E0E0',
    },
    status: {
      success: '#5A8A72',
      warning: '#D4B896',
      danger: '#C26B78',
      info: '#6BA3BE',
      success15: 'rgba(90, 138, 114, 0.15)',
      warning15: 'rgba(212, 184, 150, 0.15)',
      danger15: 'rgba(194, 107, 120, 0.15)',
      info15: 'rgba(107, 163, 190, 0.15)',
    },
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
      outlier: '#FFFFCC',
      pareto: '#ffdebe',
      excluded: '#F5F5F5',
      multiple: '#ffcaca',
    },
  },
};

export default softPastelTheme;
