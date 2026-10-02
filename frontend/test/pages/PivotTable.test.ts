/**
 * Unit tests for PivotTable page optional resultId handling
 * @module test/pages/PivotTable
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { reactive } from 'vue';
import PivotTable from '../../src/pages/PivotTable.vue';
import { usePivotStore } from '../../src/stores/pivot.js';
import {
  fetchAllTransactions,
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
  fetchAllTransactions: vi.fn(),
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
  original_category_id: null,
  original_notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
});

describe('PivotTable.vue', () => {
  let pinia: Pinia;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockRoute.params = {};
    mockRoute.query = {};
    pinia = createPinia();
    setActivePinia(pinia);
    vi.mocked(fetchCategories).mockResolvedValue([]);
    vi.mocked(fetchCostOfLivingCategories).mockResolvedValue([]);
  });

  const mountPage = (): VueWrapper => shallowMount(PivotTable, { global: { plugins: [pinia] } });

  it('fetches all transactions without result_id when resultId is undefined', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    await mountPage();
    await flushPromises();

    expect(fetchAllTransactions).toHaveBeenCalledWith(undefined);
  });

  it('fetches filtered transactions when resultId is defined', async () => {
    mockRoute.query = { resultId: 'r1' };
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(fetchAllTransactions).toHaveBeenCalledWith('r1');
    expect(wrapper.text()).not.toContain('All Transactions');
  });

  it('shows the "All Transactions" title hint when no resultId is given', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue({
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

  it('shows a truncation warning when total_count exceeds the fetched rows', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 500,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Too many transactions to display');
    expect(wrapper.text()).toContain('1 / 500');
  });

  it('stores display values without currency prefix', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    await mountPage();
    await flushPromises();

    const pivotStore = usePivotStore();
    const accounts = pivotStore.resultsData?.accounts ?? [];
    expect(accounts).toHaveLength(1);

    const rows = accounts[0].data ?? [];
    expect(rows).toHaveLength(1);
    expect(rows[0].total.display).toBe('-10.50');
    expect(rows[0].total.display).not.toContain('EUR');
    expect(rows[0].details[0].amount.display).toBe('-10.50');
    expect(rows[0].details[0].amount.display).not.toContain('EUR');
  });
});
