/**
 * Unit tests for statistical analysis functionality
 * @module test/statistical-analysis
 */

import { expect, test, beforeEach, afterEach } from 'vitest';
import { updateCellHighlights, initStatisticalAnalysis } from '../src/js/statistical-analysis';

/**
 * Create a test DOM structure with tables
 */
function createTestDom() {
  document.body.innerHTML = `
    <main>
      <button id="recalculate-btn">
        <span class="spinner-border d-none"></span>
        <span>Recalculate</span>
      </button>
      <button id="reset-btn">Reset</button>
      <table data-datatable="true">
        <thead>
          <tr>
            <th>Category</th>
            <th>Jan</th>
            <th>Feb</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Food</td>
            <td>100</td>
            <td>150</td>
          </tr>
          <tr>
            <td>Transport</td>
            <td>50</td>
            <td>60</td>
          </tr>
        </tbody>
      </table>
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

test('updateCellHighlights applies correct highlight class', () => {
  updateCellHighlights({ 'Jan_Food': 'outlier' });

  const cell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  expect(cell?.classList.contains('highlight-outlier')).toBe(true);
});

test('updateCellHighlights removes existing highlights', () => {
  const cell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  if (cell) cell.classList.add('highlight-pareto');

  updateCellHighlights({ 'Jan_Food': 'outlier' });

  expect(cell?.classList.contains('highlight-pareto')).toBe(false);
  expect(cell?.classList.contains('highlight-outlier')).toBe(true);
});

test('updateCellHighlights handles multiple highlights', () => {
  updateCellHighlights({
    'Jan_Food': 'outlier',
    'Feb_Transport': 'pareto'
  });

  const foodJanCell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  const transportFebCell = document.querySelector('tbody tr:nth-child(2) td:nth-child(3)');

  expect(foodJanCell?.classList.contains('highlight-outlier')).toBe(true);
  expect(transportFebCell?.classList.contains('highlight-pareto')).toBe(true);
});

test('updateCellHighlights handles invalid key format', () => {
  updateCellHighlights({ 'invalid_key': 'outlier' });

  const cells = document.querySelectorAll('[class*="highlight-"]');
  expect(cells.length).toBe(0);
});

test('initStatisticalAnalysis marks buttons as initialized', () => {
  initStatisticalAnalysis();

  const recalculateBtn = document.getElementById('recalculate-btn');
  const resetBtn = document.getElementById('reset-btn');

  expect(recalculateBtn?.dataset.initialized).toBe('true');
  expect(resetBtn?.dataset.initialized).toBe('true');
});

test('updateCellHighlights handles missing table elements', () => {
  document.body.innerHTML = '<table data-datatable="true"></table>';

  expect(() => updateCellHighlights({ 'Jan_Food': 'outlier' })).not.toThrow();
});

test('updateCellHighlights handles empty highlights object', () => {
  expect(() => updateCellHighlights({})).not.toThrow();
});

test('updateCellHighlights works with multiple tables', () => {
  document.body.innerHTML = `
    <table data-datatable="true">
      <thead><tr><th>Category</th><th>Jan</th></tr></thead>
      <tbody><tr><td>Food</td><td>100</td></tr></tbody>
    </table>
    <table data-datatable="true">
      <thead><tr><th>Category</th><th>Jan</th></tr></thead>
      <tbody><tr><td>Food</td><td>200</td></tr></tbody>
    </table>
  `;

  updateCellHighlights({ 'Jan_Food': 'excluded' });

  const cells = document.querySelectorAll('td:nth-child(2)');
  cells.forEach(cell => {
    expect(cell.classList.contains('highlight-excluded')).toBe(true);
  });
});