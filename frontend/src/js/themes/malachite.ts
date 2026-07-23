/**
 * Malachite theme for What's the Damage
 * Vibrant, energetic theme with bright green and warm accent colors
 */

import type { Theme } from './theme.types.js';

const malachiteTheme: Theme = {
  id: 'malachite',
  name: 'Malachite',
  description: 'Vibrant, energetic theme with bright green and warm accent colors',
  colors: {
    surface: {
      primary: '#04e762',
      secondary: '#f5b700',
      elevated: '#f8f9fa',
      base: '#ffffff',
      primary10: 'rgba(4, 231, 98, 0.10)',
    },
    text: {
      primary: '#04e762',
      secondary: '#f5b700',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#212529',
      onLight05: 'rgba(33, 37, 41, 0.05)',
      onLight10: 'rgba(33, 37, 41, 0.10)',
    },
    border: {
      primary: '#04e762',
      secondary: '#f5b700',
      subtle: '#dc0073',
    },
    status: {
      success: '#89fc00',
      warning: '#f5b700',
      danger: '#dc0073',
      info: '#008bf8',
      success15: 'rgba(137, 252, 0, 0.15)',
      warning15: 'rgba(245, 183, 0, 0.15)',
      danger15: 'rgba(220, 0, 115, 0.15)',
      info15: 'rgba(0, 139, 248, 0.15)',
    },
    chart: {
      category: [
        '#04e762', // malachite
        '#008bf8', // brilliant-azure
        '#dc0073', // fuchsia-flame
        '#f5b700', // amber-flame
        '#89fc00', // lime-flash
        '#0066cc', // malachite darker variant
        '#00aaff', // brilliant-azure lighter variant
        '#ff66b3', // fuchsia-flame lighter variant
        '#ffcc00', // amber-flame lighter variant
        '#66cc00', // lime-flash darker variant
        '#004d33', // malachite very dark
        '#99ccff', // brilliant-azure very light
      ],
      pie: [
        '#04e762',
        '#008bf8',
        '#dc0073',
        '#f5b700',
        '#89fc00',
        '#0066cc',
        '#00aaff',
        '#ff66b3',
        '#ffcc00',
        '#66cc00',
        '#004d33',
        '#99ccff',
      ],
      trendline: '#dc0073',
    },
    highlight: {
      outlier: '#ffdb70',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#ff66b3',
    },
  },
};

export default malachiteTheme;
