/**
 * Unit tests for index page functionality
 * @module test/index
 */

import { describe, it, expect, vi } from 'vitest';
import { clearForm } from '../src/js/index';

describe('index.ts', () => {
  describe('clearForm', () => {
    it('should call fetch with POST method to /clear', () => {
      const mockFetch = vi.fn(() => Promise.resolve({ ok: true } as Response));
      globalThis.fetch = mockFetch as typeof fetch;

      clearForm();

      expect(mockFetch).toHaveBeenCalledWith('/clear', { method: 'POST' });
    });

    it('should reload page when response is ok', async () => {
      // Create a mock reload function
      const reloadMock = vi.fn();

      // Store original location for properties we need
      const originalLocation = globalThis.location;

      // Create a minimal mock location with just what we need
      const mockLocation = {
        reload: reloadMock,
        href: originalLocation.href,
        origin: originalLocation.origin,
        protocol: originalLocation.protocol,
        host: originalLocation.host,
        hostname: originalLocation.hostname,
        port: originalLocation.port,
        pathname: originalLocation.pathname,
        search: originalLocation.search,
        hash: originalLocation.hash
      };

      // Stub location on both window and globalThis for compatibility
      vi.stubGlobal('location', mockLocation);
      vi.stubGlobal('window', { location: mockLocation });

      // Mock fetch to return a successful response
      globalThis.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
        } as Response)
      );

      // Call the function to trigger the fetch
      clearForm();

      // Wait for the promise chain to complete
      await new Promise(setImmediate);

      expect(reloadMock).toHaveBeenCalled();

      // Restore
      vi.unstubAllGlobals();
    });

    it('should handle fetch errors gracefully', async () => {
      // Spy on console.error
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock fetch to reject with an error
      globalThis.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

      clearForm();

      // Wait for the promise chain to complete
      await new Promise(setImmediate);

      // Check the spy was called before restoring
      expect(consoleError).toHaveBeenCalledWith('Error clearing form:', expect.any(Error));
      consoleError.mockRestore();
    });
  });
});