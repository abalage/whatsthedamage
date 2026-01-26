import { expect, vi } from 'vitest';

// Add global DOM elements for testing
const { JSDOM } = require('jsdom');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
// @ts-ignore - DOMWindow from JSDOM is not fully compatible with Window & globalThis
globalThis.window = dom.window;
// @ts-ignore - DOMWindow.document is compatible
globalThis.document = dom.window.document;
// @ts-ignore - DOMWindow.HTMLElement is compatible
globalThis.HTMLElement = dom.window.HTMLElement;

// Mock global functions that might be used in tests
globalThis.exportCsvText = 'Export CSV';
globalThis.exportExcelText = 'Export Excel';

// Note: window.location.reload cannot be mocked in setup due to JSDOM restrictions.
// Tests will mock it individually as needed.

// Add Vitest matchers
expect.extend({
  /**
   * @param {Element | Document | null | undefined} container
   */
  toBeInDOM(container) {
    if (!container?.contains) {
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
// @ts-ignore - Mocking fetch with simplified response object
globalThis.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    headers: new Headers(),
    status: 200,
    statusText: 'OK',
    redirected: false,
    type: 'basic',
    url: '',
    clone: () => this,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(''),
  }),
);
