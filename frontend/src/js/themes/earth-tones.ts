/**
 * Gentle Earth Tones theme for What's the Damage
 * Natural, organic, balanced with olive and taupe
 */

import type { Theme } from './theme.types.js';

const earthTonesTheme: Theme = {
  id: 'earth-tones',
  name: 'Gentle Earth Tones',
  description: 'Natural, organic, balanced with olive and taupe',
  colors: {
    surface: {
      primary: '#7BA05B',
      secondary: '#88A47C',
      elevated: '#F5F0E8',
      base: '#FFFFFF',
      primary10: 'rgba(123, 160, 91, 0.10)',
    },
    text: {
      primary: '#7BA05B',
      secondary: '#88A47C',
      onPrimary: '#FFFFFF',
      onDark: '#FFFFFF',
      onLight: '#4A4238',
      onLight05: 'rgba(74, 66, 56, 0.05)',
      onLight10: 'rgba(74, 66, 56, 0.10)',
    },
    border: {
      primary: '#7BA05B',
      secondary: '#88A47C',
      subtle: '#D4C4A8',
    },
    status: {
      success: '#6B8A5F',
      warning: '#C9B488',
      danger: '#B48EAD',
      info: '#92B4A7',
      success15: 'rgba(107, 138, 95, 0.15)',
      warning15: 'rgba(201, 180, 136, 0.15)',
      danger15: 'rgba(180, 142, 173, 0.15)',
      info15: 'rgba(146, 180, 167, 0.15)',
    },
    chart: {
      category: [
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
};

export default earthTonesTheme;
