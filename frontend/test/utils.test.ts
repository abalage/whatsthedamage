/**
 * Unit tests for utility functions
 * @module test/utils
 */

import { expect, test, vi, beforeEach, afterEach } from 'vitest';
import { showNotification } from '../src/js/utils';

/**
 * Create a test DOM structure
 */
function createTestDom() {
  document.body.innerHTML = `
    <main>
      <div>Existing content</div>
    </main>
  `;
}

/**
 * Clean up DOM after tests
 */
function cleanupDom() {
  document.body.innerHTML = '';
}

beforeEach(() => {
  createTestDom();
});

afterEach(() => {
  cleanupDom();
});

test('showNotification creates alert element with correct class', () => {
  showNotification('Test message', 'success');

  const alert = document.querySelector('.alert');
  expect(alert).toBeTruthy();
  expect(alert?.className).toContain('alert-success');
});

test('showNotification displays correct message', () => {
  const message = 'Custom test message';
  showNotification(message, 'info');

  const alert = document.querySelector('.alert');
  expect(alert?.textContent).toContain(message);
});

test('showNotification creates dismissible alert', () => {
  showNotification('Test', 'danger');

  const alert = document.querySelector('.alert');
  expect(alert?.className).toContain('alert-dismissible');
  expect(alert?.className).toContain('fade');
  expect(alert?.className).toContain('show');
});

test('showNotification includes close button', () => {
  showNotification('Test', 'warning');

  const alert = document.querySelector('.alert');
  const closeButton = alert?.querySelector('.btn-close');
  expect(closeButton).toBeTruthy();
});

test('showNotification auto-dismisses after timeout', () => {
  vi.useFakeTimers();

  showNotification('Test', 'success');
  const alert = document.querySelector('.alert');
  expect(alert?.className).toContain('show');

  // Fast-forward time
  vi.advanceTimersByTime(5000);

  expect(alert?.className).not.toContain('show');

  vi.useRealTimers();
});

test('showNotification adds alert to beginning of main element', () => {
  const main = document.querySelector('main');
  const firstChild = main?.firstChild;

  showNotification('Test', 'info');
  const alert = document.querySelector('.alert');

  expect(main?.firstChild).not.toBe(firstChild);
  // In jsdom, the alert is inserted before the first child
  expect(alert?.nextSibling).toBe(firstChild);
});

test('showNotification handles missing main element gracefully', () => {
  document.body.innerHTML = '';
  expect(() => showNotification('Test', 'success')).not.toThrow();
});