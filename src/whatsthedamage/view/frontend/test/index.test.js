import { describe, it, expect, vi } from 'vitest';
import { clearForm } from '../src/js/index';

describe('index.js', () => {
  describe('clearForm', () => {
    it('should call fetch with POST method to /clear', async () => {
      const mockFetch = vi.fn(() => Promise.resolve({ ok: true }));
      global.fetch = mockFetch;

      await clearForm();

      expect(mockFetch).toHaveBeenCalledWith('/clear', { method: 'POST' });
    });

    it('should reload page when response is ok', async () => {
      // Mock window.location.reload
      const originalReload = window.location.reload;
      const mockReload = vi.fn();
      window.location.reload = mockReload;

      global.fetch = vi.fn(() => Promise.resolve({ ok: true }));

      await clearForm();
      expect(mockReload).toHaveBeenCalled();

      // Restore original
      window.location.reload = originalReload;
    });

    it('should handle fetch errors gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      global.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

      await clearForm();
      expect(consoleError).toHaveBeenCalledWith('Error clearing form:', expect.any(Error));

      consoleError.mockRestore();
    });
  });
});
