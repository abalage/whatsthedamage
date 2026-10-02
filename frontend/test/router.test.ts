/**
 * Unit tests for router route definitions and the unknown-path catch-all
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

describe('unknown routes', () => {
  it('redirects /results/<uuid> (removed legacy URL) to the index page', async () => {
    await router.push('/results/123e4567-e89b-12d3-a456-426614174000');
    expect(router.currentRoute.value.name).toBe('index');
  });

  it('redirects /details (removed legacy URL) to the index page', async () => {
    await router.push('/details');
    expect(router.currentRoute.value.name).toBe('index');
  });

  it('redirects arbitrary unknown paths to the index page', async () => {
    await router.push('/results/accounts');
    expect(router.currentRoute.value.name).toBe('index');

    await router.push('/completely/unknown/path');
    expect(router.currentRoute.value.name).toBe('index');
  });
});
