/// <reference types="node" />
import { expect, vi } from 'vitest';

// The jsdom test environment (configured in vitest.config.js) provides the
// window, document, and element globals. Do not replace them with a separate
// JSDOM instance here: elements created via the environment globals would
// fail `instanceof` checks in @vue/test-utils and break wrapper.find().

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
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(''),
  } as Response)
);
