/**
 * Tiger Flame theme for What's the Damage
 * Warm, energetic theme with orange-red and earth tone colors
 */

import type { Theme } from './theme.types.js';

const tigerFlameTheme: Theme = {
  id: 'tiger-flame',
  name: 'Tiger Flame',
  description: 'Warm, energetic theme with orange-red and earth tone colors',
  colors: {
    surface: {
      primary: '#fe5d26',
      secondary: '#f2c078',
      elevated: '#faedca',
      base: '#ffffff',
      primary10: 'rgba(254, 93, 38, 0.10)',
    },
    text: {
      primary: '#fe5d26',
      secondary: '#f2c078',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#3d2c1a',
      onLight05: 'rgba(61, 44, 26, 0.05)',
      onLight10: 'rgba(61, 44, 26, 0.10)',
    },
    border: {
      primary: '#fe5d26',
      secondary: '#f2c078',
      subtle: '#c1dbb3',
    },
    status: {
      success: '#7ebc89',
      warning: '#f2c078',
      danger: '#fe5d26',
      info: '#4a7c59',
      success15: 'rgba(126, 188, 137, 0.15)',
      warning15: 'rgba(242, 192, 120, 0.15)',
      danger15: 'rgba(254, 93, 38, 0.15)',
      info15: 'rgba(74, 124, 89, 0.15)',
    },
    chart: {
      category: [
        '#fe5d26', // tiger-flame
        '#f2c078', // sunlit-clay
        '#faedca', // pearl-beige
        '#c1dbb3', // tea-green
        '#7ebc89', // emerald
        '#e64a1a', // tiger-flame darker
        '#d8a860', // sunlit-clay darker
        '#e0d5b8', // pearl-beige darker
        '#a8c498', // tea-green darker
        '#68a374', // emerald darker
        '#cc3a10', // tiger-flame very dark
        '#f8d090', // sunlit-clay lighter
      ],
      pie: [
        '#fe5d26',
        '#f2c078',
        '#faedca',
        '#c1dbb3',
        '#7ebc89',
        '#e64a1a',
        '#d8a860',
        '#e0d5b8',
        '#a8c498',
        '#68a374',
        '#cc3a10',
        '#f8d090',
      ],
      trendline: '#7ebc89',
    },
    highlight: {
      outlier: '#ffdb70',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#ff6b35',
    },
  },
};

export default tigerFlameTheme;
