/**
 * Unit tests for the useTablePagination composable
 * @module test/composables/useTablePagination
 */

import { describe, it, expect } from 'vitest';
import { ref } from 'vue';
import { useTablePagination } from '../../src/composables/useTablePagination';

describe('useTablePagination', () => {
  it('computes page count from item count and page size', () => {
    const pagination = useTablePagination(() => 55, () => 25);
    expect(pagination.totalItems.value).toBe(55);
    expect(pagination.pageSize.value).toBe(25);
    expect(pagination.totalPages.value).toBe(3);
  });

  it('goToPage moves within the valid range only', () => {
    const pagination = useTablePagination(() => 50, () => 25);
    pagination.goToPage(2);
    expect(pagination.currentPage.value).toBe(2);
    pagination.goToPage(5);
    expect(pagination.currentPage.value).toBe(2);
    pagination.goToPage(0);
    expect(pagination.currentPage.value).toBe(2);
  });

  it('reset returns to the first page', () => {
    const pagination = useTablePagination(() => 50, () => 25);
    pagination.goToPage(2);
    pagination.reset();
    expect(pagination.currentPage.value).toBe(1);
  });

  it('lists all pages when the count fits the visible window', () => {
    const pagination = useTablePagination(() => 100, () => 25);
    expect(pagination.paginationPages.value).toEqual([1, 2, 3, 4]);
  });

  it('inserts ellipsis around the current page for long lists', () => {
    const pagination = useTablePagination(() => 1000, () => 10);
    expect(pagination.paginationPages.value).toEqual([1, 2, 3, 4, 5, 6, '...', 100]);

    pagination.goToPage(50);
    expect(pagination.paginationPages.value).toEqual([1, '...', 47, 48, 49, 50, 51, 52, 53, '...', 100]);

    pagination.goToPage(100);
    expect(pagination.paginationPages.value).toEqual([1, '...', 95, 96, 97, 98, 99, 100]);
  });

  it('reacts to a changing item count', () => {
    const items = ref(100);
    const pagination = useTablePagination(() => items.value, () => 25);
    expect(pagination.totalPages.value).toBe(4);
    items.value = 10;
    expect(pagination.totalPages.value).toBe(1);
  });
});
