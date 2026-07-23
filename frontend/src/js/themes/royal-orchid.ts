/**
 * Royal Orchid theme for What's the Damage
 * Regal, elegant theme with purple and orange accent colors
 */

import type { Theme } from './theme.types.js';

const royalOrchidTheme: Theme = {
  id: 'royal-orchid',
  name: 'Royal Orchid',
  description: 'Regal, elegant theme with purple and orange accent colors',
  colors: {
    surface: {
      primary: '#791e94',
      secondary: '#de6449',
      elevated: '#ffb2e6',
      base: '#ffffff',
      primary10: 'rgba(121, 30, 148, 0.10)',
    },
    text: {
      primary: '#791e94',
      secondary: '#de6449',
      onPrimary: '#ffffff',
      onDark: '#ffffff',
      onLight: '#2e1a3a',
      onLight05: 'rgba(46, 26, 58, 0.05)',
      onLight10: 'rgba(46, 26, 58, 0.10)',
    },
    border: {
      primary: '#791e94',
      secondary: '#de6449',
      subtle: '#407899',
    },
    status: {
      success: '#99c24d',
      warning: '#de6449',
      danger: '#791e94',
      info: '#407899',
      success15: 'rgba(153, 194, 77, 0.15)',
      warning15: 'rgba(222, 100, 73, 0.15)',
      danger15: 'rgba(121, 30, 148, 0.15)',
      info15: 'rgba(64, 120, 153, 0.15)',
    },
    chart: {
      category: [
        '#791e94', // royal-orchid
        '#de6449', // burnt-peach
        '#407899', // cerulean
        '#99c24d', // yellow-green
        '#ffb2e6', // blush-pop
        '#5a1470', // royal-orchid darker
        '#c24a34', // burnt-peach darker
        '#2c587a', // cerulean darker
        '#7ab83d', // yellow-green darker
        '#ff88d2', // blush-pop darker
        '#3a0a4a', // royal-orchid very dark
        '#e67a5c', // burnt-peach lighter
      ],
      pie: [
        '#791e94',
        '#de6449',
        '#407899',
        '#99c24d',
        '#ffb2e6',
        '#5a1470',
        '#c24a34',
        '#2c587a',
        '#7ab83d',
        '#ff88d2',
        '#3a0a4a',
        '#e67a5c',
      ],
      trendline: '#99c24d',
    },
    highlight: {
      outlier: '#ffdb70',
      pareto: '#ffc697',
      excluded: '#b2b2b2',
      multiple: '#de6449',
    },
  },
};

export default royalOrchidTheme;
