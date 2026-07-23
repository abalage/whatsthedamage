/**
 * Baltic Blue theme for What's the Damage
 * Cool, professional theme with blue and green accent colors
 */

import type { Theme } from './theme.types.js';

const balticBlueTheme: Theme = {
  id: 'baltic-blue',
  name: 'Baltic Blue',
  description: 'Cool, professional theme with blue and green accent colors',
  colors: {
    surface: {
      primary: '#05668d',
      secondary: '#427aa1',
      elevated: '#ebf2fa',
      base: '#ffffff',
      primary10: 'rgba(5, 102, 141, 0.10)',
    },
    text: {
      primary: '#05668d',
      secondary: '#427aa1',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#1a2a3a',
      onLight05: 'rgba(26, 42, 58, 0.05)',
      onLight10: 'rgba(26, 42, 58, 0.10)',
    },
    border: {
      primary: '#05668d',
      secondary: '#427aa1',
      subtle: '#9bb8c8',
    },
    status: {
      success: '#679436',
      warning: '#a5be00',
      danger: '#e74c3c',
      info: '#2980b9',
      success15: 'rgba(103, 148, 54, 0.15)',
      warning15: 'rgba(165, 190, 0, 0.15)',
      danger15: 'rgba(231, 76, 60, 0.15)',
      info15: 'rgba(41, 128, 185, 0.15)',
    },
    chart: {
      category: [
        '#05668d', // baltic-blue
        '#427aa1', // rich-cerulean
        '#ebf2fa', // alice-blue
        '#679436', // sage-green
        '#a5be00', // lime-moss
        '#1a4d68', // baltic-blue darker
        '#346187', // rich-cerulean darker
        '#c5d9e8', // alice-blue darker
        '#527a2c', // sage-green darker
        '#8ab300', // lime-moss darker
        '#003d56', // baltic-blue very dark
        '#5da0c8', // rich-cerulean lighter
      ],
      pie: [
        '#05668d',
        '#427aa1',
        '#ebf2fa',
        '#679436',
        '#a5be00',
        '#1a4d68',
        '#346187',
        '#c5d9e8',
        '#527a2c',
        '#8ab300',
        '#003d56',
        '#5da0c8',
      ],
      trendline: '#679436',
    },
    highlight: {
      outlier: '#679436',
      pareto: '#a5be00',
      excluded: '#b2b2b2',
      multiple: '#e74c3c',
      // outlier: '#ffdb70',
      // pareto: '#ffc697',
      // excluded: '#b2b2b2',
      // multiple: '#e74c3c',
    },
  },
};

export default balticBlueTheme;
