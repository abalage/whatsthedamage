/**
 * Unit tests for CategoryMonthTransactions page amount display formatting
 * @module test/pages/CategoryMonthTransactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import CategoryMonthTransactions from '../../src/pages/CategoryMonthTransactions.vue';
import { fetchCategoryMonthTransactions } from '../../src/js/api.js';
import type { TransactionListItem, TransactionListResponse } from '../../src/types/api.js';

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
  fetchCategoryMonthTransactions: vi.fn(),
}));

const makeTransaction = (id: number, amount: number): TransactionListItem => ({
  id,
  user_id: 1,
  result_id: 'r1',
  date: '2026-01-15',
  transaction_type: 'debit',
  original_partner: 'Store',
  amount,
  currency: 'HUF',
  account: 'acc1',
  deduplication_hash: `hash-${id}`,
  category_id: 'grocery',
  partner: null,
  notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
});

const makeResponse = (): TransactionListResponse => ({
  transactions: [makeTransaction(1, -10.5), makeTransaction(2, -20)],
  total_count: 2,
  limit: 10000,
  offset: 0,
});

describe('CategoryMonthTransactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
  });

  const mountPage = (): VueWrapper => shallowMount(CategoryMonthTransactions, { global: { plugins: [createPinia()] } });

  it('renders transaction amounts without currency next to the numbers', async () => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ amount_display: string }>;
    }).tableData;

    expect(tableData).toHaveLength(2);
    expect(tableData[0].amount_display).toBe('-10.50');
    expect(tableData[1].amount_display).toBe('-20.00');
    expect(tableData[0].amount_display).not.toContain('HUF');
  });

  it('keeps the currency only in the account header, not in the amounts', async () => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const accountCurrency = (wrapper.vm as unknown as {
      accountCurrency: string | null;
    }).accountCurrency;

    expect(accountCurrency).toBe('HUF');
    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ amount_display: string }>;
    }).tableData;
    expect(tableData[0].amount_display).toBe('-10.50');
  });
});
