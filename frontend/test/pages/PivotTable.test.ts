/**
 * Unit tests for PivotTable page optional resultId handling
 * @module test/pages/PivotTable
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import PivotTable from '../../src/pages/PivotTable.vue';
import {
  fetchTransactionsByResult,
  fetchCategories,
  fetchCostOfLivingCategories,
} from '../../src/js/api.js';
import type { TransactionListItem } from '../../src/types/api.js';

const mockRoute = reactive<{ params: Record<string, unknown>; query: Record<string, unknown> }>({
  params: {},
  query: {},
});

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: () => mockRoute,
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../../src/js/api.js', () => ({
  fetchTransactionsByResult: vi.fn(),
  fetchCategories: vi.fn(),
  fetchCostOfLivingCategories: vi.fn(),
}));

const makeTransaction = (id: number): TransactionListItem => ({
  id,
  user_id: 1,
  result_id: 'r1',
  date: '2026-01-15',
  transaction_type: 'debit',
  original_partner: 'Store',
  amount: -10.5,
  currency: 'EUR',
  account: 'acc1',
  deduplication_hash: `hash-${id}`,
  category_id: 'food',
  partner: null,
  notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
});

describe('PivotTable.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockRoute.params = {};
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
    vi.mocked(fetchCostOfLivingCategories).mockResolvedValue([]);
  });

  const mountPage = (): VueWrapper => shallowMount(PivotTable, { global: { plugins: [createPinia()] } });

  it('fetches all transactions without result_id when resultId is undefined', async () => {
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    await mountPage();
    await flushPromises();

    expect(fetchTransactionsByResult).toHaveBeenCalledWith(undefined, { limit: 10000 });
  });

  it('fetches filtered transactions when resultId is defined', async () => {
    mockRoute.query = { resultId: 'r1' };
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(fetchTransactionsByResult).toHaveBeenCalledWith('r1', { limit: 10000 });
    expect(wrapper.text()).not.toContain('All Transactions');
  });

  it('shows the "All Transactions" title hint when no resultId is given', async () => {
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect((wrapper.vm as unknown as { headerTitle: string }).headerTitle)
      .toContain('All Transactions');
  });
});
