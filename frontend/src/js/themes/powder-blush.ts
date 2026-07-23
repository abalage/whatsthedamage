/**
 * Powder Blush theme for What's the Damage
 * Soft, feminine theme with pink and coral accent colors
 */

import type { Theme } from './theme.types.js';

const powderBlushTheme: Theme = {
  id: 'powder-blush',
  name: 'Powder Blush',
  description: 'Soft, feminine theme with pink and coral accent colors',
  colors: {
    surface: {
      primary: '#ffa69e',
      secondary: '#ff7e6b',
      elevated: '#fff7f8',
      base: '#ffffff',
      primary10: 'rgba(255, 166, 158, 0.10)',
    },
    text: {
      primary: '#8c5e58',
      secondary: '#ff7e6b',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#4a3a38',
      onLight05: 'rgba(74, 58, 56, 0.05)',
      onLight10: 'rgba(74, 58, 56, 0.10)',
    },
    border: {
      primary: '#ffa69e',
      secondary: '#ff7e6b',
      subtle: '#99c24d',
    },
    status: {
      success: '#99c24d',
      warning: '#ff7e6b',
      danger: '#ffa69e',
      info: '#407899',
      success15: 'rgba(153, 194, 77, 0.15)',
      warning15: 'rgba(255, 126, 107, 0.15)',
      danger15: 'rgba(255, 166, 158, 0.15)',
      info15: 'rgba(64, 120, 153, 0.15)',
    },
    chart: {
      category: [
        '#ffa69e', // powder-blush
        '#ff7e6b', // salmon
        '#8c5e58', // smoky-rose
        '#99c24d', // yellow-green
        '#fff7f8', // snow
        '#e6958c', // powder-blush darker
        '#e66d5a', // salmon darker
        '#7a4a44', // smoky-rose darker
        '#88b03d', // yellow-green darker
        '#ffe0e8', // snow darker (very light pink)
        '#cc7a6c', // powder-blush much darker
        '#ff9a85', // salmon lighter
      ],
      pie: [
        '#ffa69e',
        '#ff7e6b',
        '#8c5e58',
        '#99c24d',
        '#fff7f8',
        '#e6958c',
        '#e66d5a',
        '#7a4a44',
        '#88b03d',
        '#ffe0e8',
        '#cc7a6c',
        '#ff9a85',
      ],
      trendline: '#99c24d',
    },
    highlight: {
      outlier: '#ffdb70',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#ff8a7a',
    },
  },
};

export default powderBlushTheme;
