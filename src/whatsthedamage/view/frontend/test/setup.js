import { expect } from 'vitest';

// Add global DOM elements for testing
const { JSDOM } = require('jsdom');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
global.window = dom.window;
global.document = dom.window.document;
global.HTMLElement = dom.window.HTMLElement;

// Mock global functions that might be used in tests
global.exportCsvText = 'Export CSV';
global.exportExcelText = 'Export Excel';

// Add Vitest matchers
expect.extend({
  toBeInDOM(container) {
    if (!container || !container.contains) {
      return {
        pass: false,
        message: () => 'Container is not a valid DOM element',
      };
    }
    return {
      pass: true,
      message: () => 'Element is in DOM',
    };
  },
});

// Mock fetch for testing
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  }),
);