/**
 * Woodpicker theme for What's the Damage
 * Woodpicker likes these colors
 */

import type { Theme } from './theme.types.js';

const pickerTheme: Theme = {
  id: 'picker',
  name: 'Woodpicker',
  description: 'Woodpicker likes these colors',
  colors: {
    surface: {
      primary: '#003f5c',
      secondary: '#2e4b7f',
      elevated: '#f8f9fa',
      base: '#FFFFFF',
      primary10: 'rgba(0, 63, 92, 0.10)',
    },
    text: {
      primary: '#003f5c',
      secondary: '#2e4b7f',
      onPrimary: '#FFFFFF',
      onDark: '#FFFFFF',
      onLight: '#001a2f',
      onLight05: 'rgba(0, 26, 47, 0.05)',
      onLight10: 'rgba(0, 26, 47, 0.10)',
    },
    border: {
      primary: '#003f5c',
      secondary: '#2e4b7f',
      subtle: '#655197',
    },
    status: {
      success: '#655197',
      warning: '#ffa600',
      danger: '#fa5972',
      info: '#003f5c',
      success15: 'rgba(101, 81, 151, 0.15)',
      warning15: 'rgba(255, 166, 0, 0.15)',
      danger15: 'rgba(250, 89, 114, 0.15)',
      info15: 'rgba(0, 63, 92, 0.15)',
    },
    chart: {
      category: [
        '#ffa600',
        '#ff7a49',
        '#fa5972',
        '#d44e90',
        '#9f509d',
        '#655197',
        '#2e4b7f',
        '#003f5c',
      ],
      pie: [
        '#ffa600',
        '#ff7a49',
        '#fa5972',
        '#d44e90',
        '#9f509d',
        '#655197',
        '#2e4b7f',
        '#003f5c',
      ],
      trendline: '#ff7a49',
    },
    highlight: {
      outlier: '#ffa600',
      pareto: '#ff7a49',
      excluded: '#b2b2b2',
      multiple: '#d44e90',
    },
  },
};

export default pickerTheme;
