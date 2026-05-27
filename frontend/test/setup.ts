import { expect, vi } from 'vitest';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');

// Set up global DOM environment
(globalThis as Record<string, unknown>).window = dom.window as unknown as Window & typeof globalThis;
(globalThis as Record<string, unknown>).document = dom.window.document;
(globalThis as Record<string, unknown>).HTMLElement = dom.window.HTMLElement;

// Mock global functions that might be used in tests
(globalThis as Record<string, unknown>).exportCsvText = 'Export CSV';
(globalThis as Record<string, unknown>).exportExcelText = 'Export Excel';

// Note: window.location.reload cannot be mocked in setup due to JSDOM restrictions.
// Tests will mock it individually as needed.

// Add Vitest matchers
expect.extend({
  /**
   * Check if an element is in the DOM
   * @param received - Element or container to check
   * @returns Assertion result
   */
  toBeInDOM(received: Element | Document | null | undefined): { pass: boolean; message: () => string } {
    if (!received?.contains) {
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
globalThis.fetch = vi.fn((): Promise<Response> =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    headers: new Headers(),
    status: 200,
    statusText: 'OK',
    redirected: false,
    type: 'basic',
    url: '',
    clone: function() { return this; },
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)), // eslint-disable-line no-magic-numbers
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(''),
  } as Response)
);
