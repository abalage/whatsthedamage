import { describe, it, expect, vi, beforeEach } from 'vitest';
import { showNotification } from '../src/js/utils';

describe('utils.js', () => {
  beforeEach(() => {
    // Set up a basic DOM
    document.body.innerHTML = `
      <main>
        <div id="content">Test content</div>
      </main>
    `;
  });

  describe('showNotification', () => {
    it('should create and display a notification element', () => {
      showNotification('Test message', 'success');

      const notification = document.querySelector('.alert');
      expect(notification).toBeTruthy();
      expect(notification.classList.contains('alert-success')).toBe(true);
      expect(notification.textContent).toContain('Test message');
    });

    it('should add notification to main element', () => {
      const main = document.querySelector('main');
      showNotification('Test message', 'danger');

      const notification = main.querySelector('.alert');
      expect(notification).toBeTruthy();
      expect(notification).toBe(main.firstChild);
    });

    it('should auto-dismiss after 5 seconds', () => {
      vi.useFakeTimers();
      showNotification('Test message', 'info');

      const notification = document.querySelector('.alert');
      expect(notification.classList.contains('show')).toBe(true);

      vi.advanceTimersByTime(5000);
      expect(notification.classList.contains('show')).toBe(false);

      vi.useRealTimers();
    });

    it('should handle missing main element gracefully', () => {
      document.body.innerHTML = '<div>No main element</div>';
      expect(() => showNotification('Test', 'warning')).not.toThrow();
    });
  });
});