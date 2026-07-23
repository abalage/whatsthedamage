/**
 * Lime Cream theme for What's the Damage
 * Soft, gentle theme with pastel green and warm neutral colors
 */

import type { Theme } from './theme.types.js';

const limeCreamTheme: Theme = {
  id: 'lime-cream',
  name: 'Lime Cream',
  description: 'Soft, gentle theme with pastel green and warm neutral colors',
  colors: {
    surface: {
      primary: '#cbe896',
      secondary: '#aac0aa',
      elevated: '#fcdfa6',
      base: '#ffffff',
      primary10: 'rgba(203, 232, 150, 0.10)',
    },
    text: {
      primary: '#6b7a5a',
      secondary: '#8a9a7a',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#4a4238',
      onLight05: 'rgba(74, 66, 56, 0.05)',
      onLight10: 'rgba(74, 66, 56, 0.10)',
    },
    border: {
      primary: '#a18276',
      secondary: '#f4b886',
      subtle: '#d4c4a8',
    },
    status: {
      success: '#a5be00',
      warning: '#f4b886',
      danger: '#c97a58',
      info: '#679436',
      success15: 'rgba(165, 190, 0, 0.15)',
      warning15: 'rgba(244, 184, 134, 0.15)',
      danger15: 'rgba(201, 122, 88, 0.15)',
      info15: 'rgba(103, 148, 54, 0.15)',
    },
    chart: {
      category: [
        '#cbe896', // lime-cream
        '#aac0aa', // ash-grey
        '#fcdfa6', // soft-peach
        '#a18276', // dusty-taupe
        '#f4b886', // light-caramel
        '#99b87a', // lime-cream darker
        '#88a08a', // ash-grey darker
        '#f0c48a', // soft-peach darker
        '#8a6a5a', // dusty-taupe darker
        '#e4a06a', // light-caramel darker
        '#b0d090', // lime-cream lighter
        '#c8d4c4', // ash-grey lighter
      ],
      pie: [
        '#cbe896',
        '#aac0aa',
        '#fcdfa6',
        '#a18276',
        '#f4b886',
        '#99b87a',
        '#88a08a',
        '#f0c48a',
        '#8a6a5a',
        '#e4a06a',
        '#b0d090',
        '#c8d4c4',
      ],
      trendline: '#a5be00',
    },
    highlight: {
      outlier: '#ffdb70',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#ffa070',
    },
  },
};

export default limeCreamTheme;
