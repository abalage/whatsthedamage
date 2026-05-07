import { expect, vi } from 'vitest';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
// @ts-expect-error - DOMWindow from JSDOM is not fully compatible with Window & globalThis
globalThis.window = dom.window;
// @ts-expect-error - DOMWindow.document is compatible
globalThis.document = dom.window.document;
// @ts-expect-error - DOMWindow.HTMLElement is compatible
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
   * @returns {{ pass: boolean; message: () => string }}
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
// @ts-expect-error - Mocking fetch with simplified response object
const EMPTY_BUFFER_SIZE = 0
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
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(EMPTY_BUFFER_SIZE)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(''),
  }),
);
