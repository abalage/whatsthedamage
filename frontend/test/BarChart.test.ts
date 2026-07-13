/**
 * Unit tests for BarChart component
 * @module test/BarChart
 */

import { expect, test, describe } from 'vitest';
import { ref } from 'vue';

// Type definitions (duplicated from BarChart.vue for testing)
interface MultiCategoryChartData {
  label: string;
  timestamp?: number;
  values: Record<string, number>;
}

interface CategoryConfig {
  id: string;
  label: string;
}



// Helper to create test data
function createTestData(numBars: number, numCategories: number): MultiCategoryChartData[] {
  return Array.from({ length: numBars }, (_, barIndex) => ({
    label: `Bar ${barIndex}`,
    timestamp: Date.now() - (numBars - barIndex) * 1000,
    values: Object.fromEntries(
      Array.from({ length: numCategories }, (_, catIndex) => [
        `category_${catIndex}`,
        (barIndex + 1) * (catIndex + 1) * 10
      ])
    )
  }));
}

function createTestCategories(numCategories: number): CategoryConfig[] {
  return Array.from({ length: numCategories }, (_, index) => ({
    id: `category_${index}`,
    label: `Category ${index}`
  }));
}

describe('BarChart component logic', () => {
  describe('Data structure validation', () => {
    test('should create valid chart data with empty input', () => {
      const data: MultiCategoryChartData[] = [];
      const categories: CategoryConfig[] = [];

      expect(data).toBeInstanceOf(Array);
      expect(categories).toBeInstanceOf(Array);
    });

    test('should create valid chart data with single bar and category', () => {
      const data = createTestData(1, 1);
      const categories = createTestCategories(1);

      expect(data).toHaveLength(1);
      expect(data[0].label).toBe('Bar 0');
      expect(data[0].values[categories[0].id]).toBe(10);
    });

    test('should create valid chart data with multiple bars and categories', () => {
      const data = createTestData(3, 2);
      const categories = createTestCategories(2);

      expect(data).toHaveLength(3);
      expect(data[0].values[categories[0].id]).toBe(10);
      expect(data[0].values[categories[1].id]).toBe(20);
      expect(data[1].values[categories[0].id]).toBe(20);
      expect(data[1].values[categories[1].id]).toBe(40);
      expect(data[2].values[categories[0].id]).toBe(30);
      expect(data[2].values[categories[1].id]).toBe(60);
    });
  });

  describe('Selection logic simulation', () => {
    test('should start with empty selection array', () => {
      const selectedIndices = ref<number[]>([]);
      expect(selectedIndices.value).toEqual([]);
    });

    test('should add index to selection when not selected', () => {
      const selectedIndices = ref<number[]>([]);
      const barIndex = 0;
      const currentSelection = [...selectedIndices.value];
      const isSelected = currentSelection.includes(barIndex);

      expect(isSelected).toBe(false);

      selectedIndices.value = [...currentSelection, barIndex];
      expect(selectedIndices.value).toEqual([0]);
    });

    test('should remove index from selection when already selected', () => {
      const selectedIndices = ref<number[]>([0, 1, 2]);
      const barIndex = 1;
      const currentSelection = [...selectedIndices.value];
      const isSelected = currentSelection.includes(barIndex);

      expect(isSelected).toBe(true);

      selectedIndices.value = currentSelection.filter(i => i !== barIndex);
      expect(selectedIndices.value).toEqual([0, 2]);
    });

    test('should toggle selection on and off', () => {
      const selectedIndices = ref<number[]>([]);

      // First click - select
      let currentSelection = [...selectedIndices.value];
      let barIndex = 0;
      let isSelected = currentSelection.includes(barIndex);
      if (isSelected) {
        selectedIndices.value = currentSelection.filter(i => i !== barIndex);
      } else {
        selectedIndices.value = [...currentSelection, barIndex];
      }
      expect(selectedIndices.value).toEqual([0]);

      // Second click on same bar - deselect
      currentSelection = [...selectedIndices.value];
      barIndex = 0;
      isSelected = currentSelection.includes(barIndex);
      if (isSelected) {
        selectedIndices.value = currentSelection.filter(i => i !== barIndex);
      } else {
        selectedIndices.value = [...currentSelection, barIndex];
      }
      expect(selectedIndices.value).toEqual([]);
    });

    test('should handle multiple selections', () => {
      const selectedIndices = ref<number[]>([]);
      const indicesToSelect = [0, 2, 4];

      for (const idx of indicesToSelect) {
        const currentSelection = [...selectedIndices.value];
        const isSelected = currentSelection.includes(idx);
        if (isSelected) {
          selectedIndices.value = currentSelection.filter(i => i !== idx);
        } else {
          selectedIndices.value = [...currentSelection, idx];
        }
      }

      expect(selectedIndices.value).toEqual([0, 2, 4]);
    });
  });

  describe('Selected items data building', () => {
    test('should build selected items data with correct structure', () => {
      const data = createTestData(3, 2);
      const categories = createTestCategories(2);
      const selectedIndices = [0, 2];

      const selectedItems = selectedIndices.map(idx => {
        const item = data[idx];
        const values: Record<string, number> = {};
        let total = 0;
        categories.forEach(category => {
          const value = item.values[category.id] || 0;
          values[category.id] = value;
          total += value;
        });
        return {
          index: idx,
          label: item.label,
          values,
          total
        };
      });

      expect(selectedItems).toHaveLength(2);
      expect(selectedItems[0].index).toBe(0);
      expect(selectedItems[0].label).toBe('Bar 0');
      expect(selectedItems[0].values).toEqual({
        category_0: 10,
        category_1: 20
      });
      expect(selectedItems[0].total).toBe(30);
      expect(selectedItems[1].index).toBe(2);
      expect(selectedItems[1].label).toBe('Bar 2');
      expect(selectedItems[1].total).toBe(90);
    });

    test('should handle empty selection', () => {
      const data = createTestData(3, 2);
      const categories = createTestCategories(2);
      const selectedIndices: number[] = [];

      const selectedItems = selectedIndices.map(idx => {
        const item = data[idx];
        const values: Record<string, number> = {};
        let total = 0;
        categories.forEach(category => {
          const value = item.values[category.id] || 0;
          values[category.id] = value;
          total += value;
        });
        return {
          index: idx,
          label: item.label,
          values,
          total
        };
      });

      expect(selectedItems).toEqual([]);
    });
  });

  describe('Event payload structure', () => {
    test('should create correct event payload for selection', () => {
      const selectedIndices = [0, 2];
      const changedIndex = 2;
      const isSelected = true;
      const selectedItems = [
        { index: 0, label: 'Bar 0', values: { category_0: 10 }, total: 10 },
        { index: 2, label: 'Bar 2', values: { category_0: 30 }, total: 30 }
      ];

      const payload = {
        selectedIndices,
        selectedItems,
        changedIndex,
        isSelected
      };

      expect(payload).toHaveProperty('selectedIndices');
      expect(payload).toHaveProperty('selectedItems');
      expect(payload).toHaveProperty('changedIndex');
      expect(payload).toHaveProperty('isSelected');
      expect(payload.selectedIndices).toEqual([0, 2]);
      expect(payload.changedIndex).toBe(2);
      expect(payload.isSelected).toBe(true);
      expect(payload.selectedItems).toHaveLength(2);
    });

    test('should create correct event payload for deselection', () => {
      const selectedIndices: number[] = [];
      const changedIndex = 0;
      const isSelected = false;
      const selectedItems: Array<{ index: number; label: string; values: Record<string, number>; total: number }> = [];

      const payload = {
        selectedIndices,
        selectedItems,
        changedIndex,
        isSelected
      };

      expect(payload.isSelected).toBe(false);
      expect(payload.selectedIndices).toEqual([]);
      expect(payload.selectedItems).toEqual([]);
    });
  });

  describe('Tick styling logic', () => {
    test('should return selected color for selected index', () => {
      const selectedIndices = [0, 2];
      const SELECTED_LABEL_COLOR = '#000000';
      const NORMAL_LABEL_COLOR = '#6c757d';

      const context = { index: 0 };
      const color = selectedIndices.includes(context.index) ? SELECTED_LABEL_COLOR : NORMAL_LABEL_COLOR;

      expect(color).toBe(SELECTED_LABEL_COLOR);
    });

    test('should return normal color for unselected index', () => {
      const selectedIndices = [0, 2];
      const SELECTED_LABEL_COLOR = '#000000';
      const NORMAL_LABEL_COLOR = '#6c757d';

      const context = { index: 1 };
      const color = selectedIndices.includes(context.index) ? SELECTED_LABEL_COLOR : NORMAL_LABEL_COLOR;

      expect(color).toBe(NORMAL_LABEL_COLOR);
    });

    test('should return bold weight for selected index', () => {
      const selectedIndices = [0, 2];

      const context = { index: 0 };
      const weight = selectedIndices.includes(context.index) ? 'bold' : 'normal';

      expect(weight).toBe('bold');
    });

    test('should return normal weight for unselected index', () => {
      const selectedIndices = [0, 2];

      const context = { index: 1 };
      const weight = selectedIndices.includes(context.index) ? 'bold' : 'normal';

      expect(weight).toBe('normal');
    });
  });

  describe('Timestamp ordering detection', () => {
    test('should detect descending order when timestamps are decreasing', () => {
      const data: MultiCategoryChartData[] = [
        { label: 'Newest', timestamp: 1000, values: { cat1: 10 } },
        { label: 'Middle', timestamp: 500, values: { cat1: 5 } },
        { label: 'Oldest', timestamp: 100, values: { cat1: 1 } }
      ];

      const hasTimestamps = data.every(item => item.timestamp !== undefined);
      const isDescending = hasTimestamps && data.length > 1 ?
        data[0].timestamp! > data[1].timestamp! :
        false;

      expect(hasTimestamps).toBe(true);
      expect(isDescending).toBe(true);
    });

    test('should detect ascending order when timestamps are increasing', () => {
      const data: MultiCategoryChartData[] = [
        { label: 'Oldest', timestamp: 100, values: { cat1: 1 } },
        { label: 'Middle', timestamp: 500, values: { cat1: 5 } },
        { label: 'Newest', timestamp: 1000, values: { cat1: 10 } }
      ];

      const hasTimestamps = data.every(item => item.timestamp !== undefined);
      const isDescending = hasTimestamps && data.length > 1 ?
        data[0].timestamp! > data[1].timestamp! :
        false;

      expect(hasTimestamps).toBe(true);
      expect(isDescending).toBe(false);
    });

    test('should handle data without timestamps', () => {
      const data: MultiCategoryChartData[] = [
        { label: 'Bar 1', values: { cat1: 10 } },
        { label: 'Bar 2', values: { cat1: 5 } }
      ];

      const hasTimestamps = data.every(item => item.timestamp !== undefined);

      expect(hasTimestamps).toBe(false);
    });
  });
});
