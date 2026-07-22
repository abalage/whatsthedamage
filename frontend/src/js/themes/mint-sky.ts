/**
 * Modern Mint & Sky theme for What's the Damage
 * Fresh, clean, contemporary with mint greens and sky blues
 */

import type { Theme } from './theme.types.js';

const mintSkyTheme: Theme = {
  id: 'mint-sky',
  name: 'Modern Mint & Sky',
  description: 'Fresh, clean, contemporary with mint greens and sky blues',
  colors: {
    surface: {
      primary: '#4ECDC4',
      secondary: '#82CAFF',
      elevated: '#F8F9FA',
      base: '#FFFFFF',
      primary10: 'rgba(78, 205, 196, 0.10)',
    },
    text: {
      primary: '#4ECDC4',
      secondary: '#82CAFF',
      onPrimary: '#FFFFFF',
      onDark: '#FFFFFF',
      onLight: '#2A3A4A',
      onLight05: 'rgba(42, 58, 74, 0.05)',
      onLight10: 'rgba(42, 58, 74, 0.10)',
    },
    border: {
      primary: '#4ECDC4',
      secondary: '#82CAFF',
      subtle: '#D4F0F5',
    },
    status: {
      success: '#3AB7A8',
      warning: '#FFD488',
      danger: '#FF8A8A',
      info: '#5FD4D0',
      success15: 'rgba(58, 183, 168, 0.15)',
      warning15: 'rgba(255, 212, 136, 0.15)',
      danger15: 'rgba(255, 138, 138, 0.15)',
      info15: 'rgba(95, 212, 208, 0.15)',
    },
    chart: {
      category: [
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
};

export default mintSkyTheme;
