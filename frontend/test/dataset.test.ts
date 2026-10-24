/**
 * Unit tests for the shared transaction dataset cache
 * @module test/dataset
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useDatasetStore } from '../src/stores/dataset';
import { fetchAllTransactions, fetchProcessingResultMetadata } from '../src/js/api';
import type { TransactionListItem, TransactionListResponse } from '../src/types/api';

vi.mock('../src/js/api', () => ({
  fetchAllTransactions: vi.fn(),
  fetchProcessingResultMetadata: vi.fn()
}));

const makeTransaction = (id: number, overrides: Partial<TransactionListItem> = {}): TransactionListItem => ({
  id,
  user_id: 1,
  result_id: null,
  date: '2025-01-15',
  transaction_type: 'type',
  original_partner: 'Store',
  amount: 100,
  currency: 'HUF',
  account: 'a1',
  deduplication_hash: `h${id}`,
  category_id: 'grocery',
  partner: null,
  notice: null,
  original_category_id: 'grocery',
  original_notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
  ...overrides
});

const makeResponse = (ids: number[]): TransactionListResponse => ({
  transactions: ids.map(id => makeTransaction(id)),
  total_count: ids.length,
  limit: ids.length,
  offset: 0
});

describe('useDatasetStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(undefined);
  });

  it('fetches the dataset once and serves repeated loads from the cache', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue(makeResponse([1, 2]));

    const store = useDatasetStore();
    const first = await store.load(undefined);
    const second = await store.load(undefined);

    expect(fetchAllTransactions).toHaveBeenCalledTimes(1);
    // Same cached entry (the reactive Map may wrap it in a proxy)
    expect(second).toStrictEqual(first);
    expect(first.transactions).toHaveLength(2);
    expect(first.metadata).toBeUndefined();
  });

  it('caches per result scope', async () => {
    vi.mocked(fetchAllTransactions).mockImplementation(async (resultId?: string) =>
      makeResponse(resultId === 'r1' ? [1] : [1, 2])
    );
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(undefined);

    const store = useDatasetStore();
    await store.load('r1');
    await store.load(undefined);

    expect(fetchAllTransactions).toHaveBeenCalledTimes(2);
    expect(fetchProcessingResultMetadata).toHaveBeenCalledWith('r1');
    expect(fetchProcessingResultMetadata).toHaveBeenCalledWith(undefined);
  });

  it('shares one request between concurrent loads of the same scope', async () => {
    let resolveFetch: (value: ReturnType<typeof makeResponse>) => void = () => {};
    vi.mocked(fetchAllTransactions).mockImplementation(
      () => new Promise(resolve => { resolveFetch = resolve; })
    );

    const store = useDatasetStore();
    const first = store.load(undefined);
    const second = store.load(undefined);
    resolveFetch(makeResponse([1]));
    const [firstEntry, secondEntry] = await Promise.all([first, second]);

    expect(fetchAllTransactions).toHaveBeenCalledTimes(1);
    expect(secondEntry).toBe(firstEntry);
  });

  it('propagates load failures without caching a partial entry', async () => {
    vi.mocked(fetchAllTransactions).mockRejectedValue(new Error('boom'));

    const store = useDatasetStore();
    await expect(store.load(undefined)).rejects.toThrow('boom');

    // A failed load is not cached and does not block a retry
    vi.mocked(fetchAllTransactions).mockResolvedValue(makeResponse([1]));
    const entry = await store.load(undefined);
    expect(entry.transactions).toHaveLength(1);
  });

  it('replaces a corrected transaction in every cached entry', async () => {
    vi.mocked(fetchAllTransactions).mockImplementation(async (resultId?: string) =>
      makeResponse(resultId === 'r1' ? [1] : [1, 2])
    );

    const store = useDatasetStore();
    const scoped = await store.load('r1');
    const all = await store.load(undefined);

    const corrected = makeTransaction(1, { category_id: 'fee', partner: 'New' });
    store.replaceTransaction(corrected);

    expect(scoped.transactions[0]).toBe(corrected);
    expect(all.transactions.find(t => t.id === 1)).toBe(corrected);
    expect(all.transactions).toHaveLength(2);
  });

  it('leaves entries without the transaction untouched', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue(makeResponse([1]));

    const store = useDatasetStore();
    const entry = await store.load(undefined);

    store.replaceTransaction(makeTransaction(99));
    expect(entry.transactions).toHaveLength(1);
    expect(entry.transactions[0].id).toBe(1);
  });

  it('invalidate drops one scope and keeps the others', async () => {
    vi.mocked(fetchAllTransactions).mockImplementation(async (resultId?: string) =>
      makeResponse(resultId === 'r1' ? [1] : [1, 2])
    );

    const store = useDatasetStore();
    await store.load('r1');
    await store.load(undefined);

    store.invalidate('r1');

    await store.load(undefined); // still cached
    await store.load('r1');      // refetched
    expect(fetchAllTransactions).toHaveBeenCalledTimes(3);
  });

  it('invalidateAll drops every scope', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue(makeResponse([1]));

    const store = useDatasetStore();
    await store.load('r1');
    await store.load(undefined);
    store.invalidateAll();

    await store.load('r1');
    expect(fetchAllTransactions).toHaveBeenCalledTimes(3);
  });

  it('exposes reactive transaction arrays shared with the pages', async () => {
    vi.mocked(fetchAllTransactions).mockResolvedValue(makeResponse([1, 2]));

    const store = useDatasetStore();
    const entry = await store.load(undefined);

    // In-place mutation through the cached array is visible on the same
    // entry reference (what the corrections composable relies on)
    entry.transactions.splice(0, 1, makeTransaction(1, { category_id: 'fee' }));
    expect(store.entries.get('__all__')?.transactions[0].category_id).toBe('fee');
  });
});
