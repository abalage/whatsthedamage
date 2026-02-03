/**
 * Unit tests for statistical analysis functionality
 * @module test/statistical-analysis
 */

import { expect, test, beforeEach, afterEach } from 'vitest';
import { updateCellHighlights, initStatisticalAnalysis } from '../src/js/statistical-analysis';

/**
 * Create a test DOM structure with tables using data-row-id attributes
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
            <td data-row-id="row-1">100</td>
            <td data-row-id="row-2">150</td>
          </tr>
          <tr>
            <td>Transport</td>
            <td data-row-id="row-3">50</td>
            <td data-row-id="row-4">60</td>
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
  updateCellHighlights({ 'row-1': 'outlier' });

  const cell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  expect(cell?.classList.contains('highlight-outlier')).toBe(true);
});

test('updateCellHighlights removes existing highlights', () => {
  const cell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  if (cell) cell.classList.add('highlight-pareto');

  updateCellHighlights({ 'row-1': 'outlier' });

  expect(cell?.classList.contains('highlight-pareto')).toBe(false);
  expect(cell?.classList.contains('highlight-outlier')).toBe(true);
});

test('updateCellHighlights handles multiple highlights', () => {
  updateCellHighlights({
    'row-1': 'outlier',
    'row-4': 'pareto'
  });

  const foodJanCell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  const transportFebCell = document.querySelector('tbody tr:nth-child(2) td:nth-child(3)');

  expect(foodJanCell?.classList.contains('highlight-outlier')).toBe(true);
  expect(transportFebCell?.classList.contains('highlight-pareto')).toBe(true);
});

test('updateCellHighlights handles invalid row ID', () => {
  updateCellHighlights({ 'invalid-row-id': 'outlier' });

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

  expect(() => updateCellHighlights({ 'row-1': 'outlier' })).not.toThrow();
});

test('updateCellHighlights handles empty highlights object', () => {
  expect(() => updateCellHighlights({})).not.toThrow();
});

test('updateCellHighlights works with multiple tables', () => {
  document.body.innerHTML = `
    <table data-datatable="true">
      <thead><tr><th>Category</th><th>Jan</th></tr></thead>
      <tbody><tr><td>Food</td><td data-row-id="row-1">100</td></tr></tbody>
    </table>
    <table data-datatable="true">
      <thead><tr><th>Category</th><th>Jan</th></tr></thead>
      <tbody><tr><td>Food</td><td data-row-id="row-1">200</td></tr></tbody>
    </table>
  `;

  updateCellHighlights({ 'row-1': 'excluded' });

  const cells = document.querySelectorAll('[data-row-id="row-1"]');
  cells.forEach(cell => {
    expect(cell.classList.contains('highlight-excluded')).toBe(true);
  });
});

test('updateCellHighlights handles all highlight types', () => {
  document.body.innerHTML = `
    <table data-datatable="true">
      <thead><tr><th>Category</th><th>Jan</th><th>Feb</th></tr></thead>
      <tbody>
        <tr><td>Food</td><td data-row-id="row-outlier">100</td><td data-row-id="row-pareto">150</td></tr>
        <tr><td>Transport</td><td data-row-id="row-excluded">50</td><td>60</td></tr>
      </tbody>
    </table>
  `;

  updateCellHighlights({
    'row-outlier': 'outlier',
    'row-pareto': 'pareto',
    'row-excluded': 'excluded'
  });

  const outlierCell = document.querySelector('[data-row-id="row-outlier"]');
  const paretoCell = document.querySelector('[data-row-id="row-pareto"]');
  const excludedCell = document.querySelector('[data-row-id="row-excluded"]');

  expect(outlierCell?.classList.contains('highlight-outlier')).toBe(true);
  expect(paretoCell?.classList.contains('highlight-pareto')).toBe(true);
  expect(excludedCell?.classList.contains('highlight-excluded')).toBe(true);
});

test('updateCellHighlights removes all highlight classes before applying new ones', () => {
  const cell = document.querySelector('tbody tr:first-child td:nth-child(2)');
  if (cell) {
    cell.classList.add('highlight-outlier');
    cell.classList.add('highlight-pareto');
  }

  updateCellHighlights({ 'row-1': 'excluded' });

  expect(cell?.classList.contains('highlight-outlier')).toBe(false);
  expect(cell?.classList.contains('highlight-pareto')).toBe(false);
  expect(cell?.classList.contains('highlight-excluded')).toBe(true);
});