/**
 * Unit tests for router route definitions and legacy redirects
 * @module test/router
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import router from '../src/router/index.js';

vi.mock('../src/js/api.js', () => ({
  getMe: vi.fn().mockResolvedValue({
    user: { id: 1, username: 'testuser', is_active: true, opt_in_sharing: false },
    csrf_token: 'token',
  }),
}));

// The router singleton uses createWebHistory, which cannot resolve URLs
// against the jsdom about:blank location; use a memory history instead
vi.mock('vue-router', async (importOriginal): Promise<Record<string, unknown>> => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    createWebHistory: (): ReturnType<typeof actual.createMemoryHistory> =>
      actual.createMemoryHistory(),
  };
});

beforeEach(() => {
  setActivePinia(createPinia());
});

describe('resultId query param routes', () => {
  it('resolves /results without a resultId', () => {
    const resolved = router.resolve('/results');
    expect(resolved.name).toBe('results');
  });

  it('resolves /results?resultId=123 with the resultId query', () => {
    const resolved = router.resolve('/results?resultId=123');
    expect(resolved.name).toBe('results');
    expect(resolved.query.resultId).toBe('123');
  });

  it('resolves /transactions without a resultId', () => {
    const resolved = router.resolve('/transactions');
    expect(resolved.name).toBe('details');
  });

  it('resolves /pivot without a resultId', () => {
    const resolved = router.resolve('/pivot');
    expect(resolved.name).toBe('pivot');
  });

  it('resolves drilldown routes without a resultId', () => {
    const resolved = router.resolve('/results/accounts/a1/categories/c1/months');
    expect(resolved.name).toBe('category-months');
    expect(resolved.params.accountId).toBe('a1');
    expect(resolved.params.categoryId).toBe('c1');
    expect(resolved.params.resultId).toBeUndefined();
  });

  it('resolves drilldown routes with a resultId query', () => {
    const resolved = router.resolve('/results/accounts/a1/categories/c1/months?resultId=r1');
    expect(resolved.name).toBe('category-months');
    expect(resolved.query.resultId).toBe('r1');
  });
});

describe('legacy path-based redirects', () => {
  it('redirects /results/:resultId to the details route with query', async () => {
    await router.push('/results/abc');
    expect(router.currentRoute.value.name).toBe('details');
    expect(router.currentRoute.value.query.resultId).toBe('abc');
  });

  it('redirects /results/:resultId/pivot to the pivot route with query', async () => {
    await router.push('/results/abc/pivot');
    expect(router.currentRoute.value.name).toBe('pivot');
    expect(router.currentRoute.value.query.resultId).toBe('abc');
  });

  it('redirects the legacy category months drilldown', async () => {
    await router.push('/results/r1/accounts/a1/categories/c1/months');
    expect(router.currentRoute.value.name).toBe('category-months');
    expect(router.currentRoute.value.params.accountId).toBe('a1');
    expect(router.currentRoute.value.params.categoryId).toBe('c1');
    expect(router.currentRoute.value.query.resultId).toBe('r1');
  });

  it('redirects the legacy month categories drilldown', async () => {
    await router.push('/results/r1/accounts/a1/months/m1/categories');
    expect(router.currentRoute.value.name).toBe('month-categories');
    expect(router.currentRoute.value.params.accountId).toBe('a1');
    expect(router.currentRoute.value.params.monthId).toBe('m1');
    expect(router.currentRoute.value.query.resultId).toBe('r1');
  });

  it('redirects the legacy category month transactions drilldown', async () => {
    await router.push('/results/r1/accounts/a1/categories/c1/months/m1/transactions');
    expect(router.currentRoute.value.name).toBe('category-month-transactions');
    expect(router.currentRoute.value.params.accountId).toBe('a1');
    expect(router.currentRoute.value.params.categoryId).toBe('c1');
    expect(router.currentRoute.value.params.monthId).toBe('m1');
    expect(router.currentRoute.value.query.resultId).toBe('r1');
  });
});
