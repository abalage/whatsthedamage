/**
 * Corporate Finance theme for What's the Damage
 * Professional, banking, trustworthy with navy and forest green
 */

import type { Theme } from './theme.types.js';

const corporateTheme: Theme = {
  id: 'corporate',
  name: 'Corporate Finance',
  description: 'Professional, banking, trustworthy with navy and forest green',
  colors: {
    surface: {
      primary: '#2C5F7A',
      secondary: '#6B8CAE',
      elevated: '#F8F9FA',
      base: '#FFFFFF',
      primary10: 'rgba(44, 95, 122, 0.10)',
    },
    text: {
      primary: '#2C5F7A',
      secondary: '#6B8CAE',
      onPrimary: '#FFFFFF',
      onDark: '#FFFFFF',
      onLight: '#1A2A3A',
      onLight05: 'rgba(26, 42, 58, 0.05)',
      onLight10: 'rgba(26, 42, 58, 0.10)',
    },
    border: {
      primary: '#2C5F7A',
      secondary: '#4A7C59',
      subtle: '#9BB8C8',
    },
    status: {
      success: '#1F4E6D',
      warning: '#C9A86B',
      danger: '#8B5A48',
      info: '#6B8CAE',
      success15: 'rgba(31, 78, 109, 0.15)',
      warning15: 'rgba(201, 168, 107, 0.15)',
      danger15: 'rgba(139, 90, 72, 0.15)',
      info15: 'rgba(107, 140, 174, 0.15)',
    },
    chart: {
      category: [
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
      outlier: '#ffd78d',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#ff5a5a',
    },
  },
};

export default corporateTheme;
