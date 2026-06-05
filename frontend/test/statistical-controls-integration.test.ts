/**
 * Integration tests for cell highlight handling in DataTables
 * Focuses on highlighting individual cells, especially when a single cell is highlighted
 * by multiple statistical algorithms, ensuring the 'highlight-multiple' CSS class is applied.
 * 
 * Rules:
 * - Single algorithm (outlier/pareto): individual class (e.g., 'highlight-outlier')
 * - Multiple algorithms: only 'highlight-multiple' class
 * - Excluded (alone or with algorithms): only 'highlight-excluded' class
 * @module test/statistical-controls-integration
 */

import { describe, expect, test, beforeEach, afterEach, vi } from 'vitest';
import { updateCellHighlights } from '../src/js/statistical-analysis.js';

/**
 * Create a test DOM structure matching Results.vue DataTable structure
 */
function createResultsTableDom(): void {
  document.body.innerHTML = `
    <div id="app">
      <table class="table table-bordered dataTable">
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
          <tr>
            <td>Utilities</td>
            <td data-row-id="row-5">200</td>
            <td data-row-id="row-6">250</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

/**
 * Clean up DOM after tests
 */
function cleanupDom(): void {
  document.body.innerHTML = '';
  vi.clearAllMocks();
}

describe('Cell Highlight Handling - highlight-multiple', () => {
  beforeEach(() => {
    createResultsTableDom();
  });

  afterEach(() => {
    cleanupDom();
  });

  describe('Single algorithm highlights', () => {
    test('applies highlight-outlier for single outlier highlight', () => {
      updateCellHighlights({ 'row-1': ['outlier'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      expect(cell?.classList.contains('highlight-outlier')).toBe(true);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(false);
    });

    test('applies highlight-pareto for single pareto highlight', () => {
      updateCellHighlights({ 'row-2': ['pareto'] });

      const cell = document.querySelector('[data-row-id="row-2"]');
      expect(cell).not.toBeNull();
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(true);
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(false);
    });
  });

  describe('Multiple algorithm highlights', () => {
    test('applies ONLY highlight-multiple when cell has both outlier and pareto', () => {
      updateCellHighlights({ 'row-1': ['outlier', 'pareto'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      // Individual algorithm classes should NOT be present
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
      // Only highlight-multiple should be present
      expect(cell?.classList.contains('highlight-multiple')).toBe(true);
      expect(cell?.classList.contains('highlight-excluded')).toBe(false);
    });

    test('applies ONLY highlight-multiple for outlier + pareto (no individual classes)', () => {
      updateCellHighlights({ 'row-1': ['outlier', 'pareto'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      
      // Verify only highlight-multiple class is present
      const highlightClasses = Array.from(cell?.classList ?? []).filter(
        cls => cls.startsWith('highlight-')
      );
      expect(highlightClasses).toEqual(['highlight-multiple']);
    });
  });

  describe('Excluded highlights', () => {
    test('applies ONLY highlight-excluded when cell has excluded only', () => {
      updateCellHighlights({ 'row-3': ['excluded'] });

      const cell = document.querySelector('[data-row-id="row-3"]');
      expect(cell).not.toBeNull();
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(true);
    });

    test('applies ONLY highlight-excluded when cell has outlier + excluded', () => {
      updateCellHighlights({ 'row-1': ['outlier', 'excluded'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      // Excluded takes precedence - no algorithm classes
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(true);
    });

    test('applies ONLY highlight-excluded when cell has outlier + pareto + excluded', () => {
      updateCellHighlights({ 'row-1': ['outlier', 'pareto', 'excluded'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      // Excluded takes precedence - no algorithm classes or highlight-multiple
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(true);
    });

    test('excluded with algorithms results in only highlight-excluded', () => {
      updateCellHighlights({ 'row-1': ['outlier', 'pareto', 'excluded'] });

      const cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell).not.toBeNull();
      
      // Verify only highlight-excluded class is present
      const highlightClasses = Array.from(cell?.classList ?? []).filter(
        cls => cls.startsWith('highlight-')
      );
      expect(highlightClasses).toEqual(['highlight-excluded']);
    });
  });

  describe('Mixed scenarios', () => {
    test('applies different highlight combinations to different cells', () => {
      updateCellHighlights({
        'row-1': ['outlier'],
        'row-2': ['pareto'],
        'row-3': ['outlier', 'pareto'],
        'row-4': ['excluded'],
        'row-5': ['outlier', 'excluded'],
        'row-6': ['outlier', 'pareto', 'excluded'],
      });

      // Single outlier
      const cell1 = document.querySelector('[data-row-id="row-1"]');
      expect(cell1?.classList.contains('highlight-outlier')).toBe(true);
      expect(cell1?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell1?.classList.contains('highlight-excluded')).toBe(false);

      // Single pareto
      const cell2 = document.querySelector('[data-row-id="row-2"]');
      expect(cell2?.classList.contains('highlight-pareto')).toBe(true);
      expect(cell2?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell2?.classList.contains('highlight-excluded')).toBe(false);

      // Multiple algorithms - only highlight-multiple
      const cell3 = document.querySelector('[data-row-id="row-3"]');
      expect(cell3?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell3?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell3?.classList.contains('highlight-multiple')).toBe(true);
      expect(cell3?.classList.contains('highlight-excluded')).toBe(false);

      // Excluded only
      const cell4 = document.querySelector('[data-row-id="row-4"]');
      expect(cell4?.classList.contains('highlight-excluded')).toBe(true);
      expect(cell4?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell4?.classList.contains('highlight-outlier')).toBe(false);

      // Outlier + excluded - only excluded
      const cell5 = document.querySelector('[data-row-id="row-5"]');
      expect(cell5?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell5?.classList.contains('highlight-excluded')).toBe(true);
      expect(cell5?.classList.contains('highlight-multiple')).toBe(false);

      // All three - only excluded
      const cell6 = document.querySelector('[data-row-id="row-6"]');
      expect(cell6?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell6?.classList.contains('highlight-pareto')).toBe(false);
      expect(cell6?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell6?.classList.contains('highlight-excluded')).toBe(true);
    });
  });

  describe('Highlight cleanup', () => {
    test('removes old highlight-multiple before applying new highlights', () => {
      // First, apply multiple highlights
      updateCellHighlights({ 'row-1': ['outlier', 'pareto'] });
      let cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-multiple')).toBe(true);
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);

      // Then, apply single highlight
      updateCellHighlights({ 'row-1': ['outlier'] });
      cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-outlier')).toBe(true);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
    });

    test('removes all old highlights when cell gets new highlight type', () => {
      // Apply outlier
      updateCellHighlights({ 'row-1': ['outlier'] });
      let cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-outlier')).toBe(true);

      // Change to pareto
      updateCellHighlights({ 'row-1': ['pareto'] });
      cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(true);
    });

    test('removes highlight-multiple when switching to excluded', () => {
      // Apply multiple algorithm highlights
      updateCellHighlights({ 'row-1': ['outlier', 'pareto'] });
      let cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-multiple')).toBe(true);

      // Switch to excluded
      updateCellHighlights({ 'row-1': ['excluded'] });
      cell = document.querySelector('[data-row-id="row-1"]');
      expect(cell?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell?.classList.contains('highlight-excluded')).toBe(true);
      expect(cell?.classList.contains('highlight-outlier')).toBe(false);
      expect(cell?.classList.contains('highlight-pareto')).toBe(false);
    });

    test('removes highlight classes from previous highlights on different cells', () => {
      // Apply highlights to multiple cells
      updateCellHighlights({
        'row-1': ['outlier', 'pareto'],
        'row-2': ['outlier'],
      });

      let cell1 = document.querySelector('[data-row-id="row-1"]');
      let cell2 = document.querySelector('[data-row-id="row-2"]');
      expect(cell1?.classList.contains('highlight-multiple')).toBe(true);
      expect(cell2?.classList.contains('highlight-outlier')).toBe(true);

      // Clear and apply new highlights
      updateCellHighlights({
        'row-3': ['pareto'],
      });

      cell1 = document.querySelector('[data-row-id="row-1"]');
      cell2 = document.querySelector('[data-row-id="row-2"]');
      const cell3 = document.querySelector('[data-row-id="row-3"]');

      // Old cells should have no highlights
      expect(cell1?.classList.contains('highlight-multiple')).toBe(false);
      expect(cell2?.classList.contains('highlight-outlier')).toBe(false);

      // New cell should have pareto highlight
      expect(cell3?.classList.contains('highlight-pareto')).toBe(true);
      expect(cell3?.classList.contains('highlight-multiple')).toBe(false);
    });
  });

  describe('Edge cases', () => {
    test('handles empty highlights object', () => {
      updateCellHighlights({});

      const cells = document.querySelectorAll('[class*="highlight-"]');
      const NO_HIGHLIGHTS = 0;
      expect(cells.length).toBe(NO_HIGHLIGHTS);
    });

    test('handles highlights for non-existent row IDs', () => {
      updateCellHighlights({ 'non-existent-row': ['outlier', 'pareto'] });

      const cells = document.querySelectorAll('[class*="highlight-"]');
      const NO_HIGHLIGHTS = 0;
      expect(cells.length).toBe(NO_HIGHLIGHTS);
    });

    test('handles multiple cells with same highlight combination', () => {
      updateCellHighlights({
        'row-1': ['outlier', 'pareto'],
        'row-2': ['outlier', 'pareto'],
        'row-3': ['outlier', 'pareto'],
      });

      const cells = document.querySelectorAll('[data-row-id]');
      const NUM_HIGHLIGHTED_CELLS = 3;
      const highlightedCells = Array.from(cells).filter(cell =>
        cell.classList.contains('highlight-multiple')
      );
      expect(highlightedCells.length).toBe(NUM_HIGHLIGHTED_CELLS);
      
      // Verify individual classes are NOT present
      highlightedCells.forEach(cell => {
        expect(cell.classList.contains('highlight-outlier')).toBe(false);
        expect(cell.classList.contains('highlight-pareto')).toBe(false);
      });
    });

    test('handles multiple cells with excluded', () => {
      updateCellHighlights({
        'row-1': ['excluded'],
        'row-2': ['outlier', 'excluded'],
        'row-3': ['outlier', 'pareto', 'excluded'],
      });

      const cells = document.querySelectorAll('[data-row-id]');
      const NUM_EXCLUDED_CELLS = 3;
      const excludedCells = Array.from(cells).filter(cell =>
        cell.classList.contains('highlight-excluded')
      );
      expect(excludedCells.length).toBe(NUM_EXCLUDED_CELLS);
      
      // Verify no algorithm classes or highlight-multiple are present
      excludedCells.forEach(cell => {
        expect(cell.classList.contains('highlight-outlier')).toBe(false);
        expect(cell.classList.contains('highlight-pareto')).toBe(false);
        expect(cell.classList.contains('highlight-multiple')).toBe(false);
      });
    });
  });
});
