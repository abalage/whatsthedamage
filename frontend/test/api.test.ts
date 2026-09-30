/**
 * Unit tests for API layer optional result_id handling
 * @module test/api
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  fetchTransactionsByResult,
  fetchAllTransactions,
  fetchCategoryMonthTransactions,
  fetchAggregatedTransactions,
  fetchProcessingResultMetadata,
  updateTransaction,
} from '../src/js/api.js';

const stubFetch = (data: unknown, ok = true): void => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok,
    status: ok ? 200 : 400,
    statusText: ok ? 'OK' : 'Bad Request',
    json: async () => data,
  } as Response)));
};

/**
 * Stub fetch with a sequence of page responses, one per request
 */
const stubFetchSequence = (pages: unknown[]): void => {
  const mock = vi.fn();
  for (const data of pages) {
    mock.mockImplementationOnce(async () => ({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => data,
    } as Response));
  }
  vi.stubGlobal('fetch', mock);
};

/**
 * Build a transaction list page response with placeholder transactions
 */
const makePage = (count: number, totalCount: number, offset: number): unknown => ({
  transactions: Array.from({ length: count }, (_, i) => ({ id: offset + i + 1 })),
  total_count: totalCount,
  limit: 2000,
  offset,
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('fetchTransactionsByResult', () => {
  it('omits result_id from the URL when resultId is undefined', async () => {
    stubFetch({ transactions: [], total_count: 0, limit: 1, offset: 0 });

    await fetchTransactionsByResult(undefined, { limit: 1 });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions?limit=1');
    expect(url).not.toContain('result_id');
  });

  it('omits result_id from the URL when resultId is an empty string', async () => {
    stubFetch({ transactions: [], total_count: 0, limit: 100, offset: 0 });

    await fetchTransactionsByResult('', {});

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions');
    expect(url).not.toContain('result_id');
  });

  it('includes result_id in the URL when resultId is provided', async () => {
    stubFetch({ transactions: [], total_count: 0, limit: 1, offset: 0 });

    await fetchTransactionsByResult('123', { limit: 1 });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions?result_id=123&limit=1');
  });
});

describe('fetchAggregatedTransactions', () => {
  it('omits result_id from the URL when result_id is undefined', async () => {
    stubFetch({
      result_id: null,
      group_by: 'month',
      groups: {},
      highlights: {},
      total_count: 0,
    });

    await fetchAggregatedTransactions({ group_by: 'month' });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions/aggregate?group_by=month');
    expect(url).not.toContain('result_id');
  });

  it('includes result_id in the URL when result_id is provided', async () => {
    stubFetch({
      result_id: '123',
      group_by: 'month',
      groups: {},
      highlights: {},
      total_count: 0,
    });

    await fetchAggregatedTransactions({ result_id: '123', group_by: 'month' });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions/aggregate?result_id=123&group_by=month');
  });
});

describe('fetchProcessingResultMetadata', () => {
  it('returns null without a request when resultId is undefined', async () => {
    stubFetch({});

    const result = await fetchProcessingResultMetadata(undefined);

    expect(result).toBe(null);
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('returns metadata when resultId is provided', async () => {
    const metadata = {
      result_id: '123',
      user_id: 1,
      csv_profile_id: null,
      row_count: 10,
      processing_time: 1,
      ml_enabled: false,
      start_date: null,
      end_date: null,
      created_at: '2026-01-01T00:00:00',
      transactions_url: '/api/v2/transactions?result_id=123',
    };
    stubFetch(metadata);

    const result = await fetchProcessingResultMetadata('123');

    expect(result).toEqual(metadata);
    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/processing-results/123');
  });

  it('URL-encodes the resultId in the metadata endpoint', async () => {
    stubFetch({});

    await fetchProcessingResultMetadata('a b/c?d');

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/processing-results/a%20b%2Fc%3Fd');
  });
});

describe('fetchAllTransactions', () => {
  it('returns a single page without further requests when all rows fit', async () => {
    stubFetchSequence([makePage(5, 5, 0)]);

    const result = await fetchAllTransactions();

    expect(result.transactions).toHaveLength(5);
    expect(result.total_count).toBe(5);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions?limit=2000&offset=0');
  });

  it('pages through the endpoint until total_count rows are collected', async () => {
    stubFetchSequence([
      makePage(2000, 2500, 0),
      makePage(500, 2500, 2000),
    ]);

    const result = await fetchAllTransactions('r1');

    expect(result.transactions).toHaveLength(2500);
    expect(result.total_count).toBe(2500);
    const urls = vi.mocked(globalThis.fetch).mock.calls.map(call => call[0] as string);
    expect(urls[0]).toBe('/api/v2/transactions?result_id=r1&limit=2000&offset=0');
    expect(urls[1]).toBe('/api/v2/transactions?result_id=r1&limit=2000&offset=2000');
  });

  it('stops at the safety cap and reports the real total_count', async () => {
    stubFetchSequence(Array.from({ length: 25 }, (_, i) => makePage(2000, 60000, i * 2000)));

    const result = await fetchAllTransactions();

    expect(result.transactions).toHaveLength(50000);
    expect(result.total_count).toBe(60000);
    expect(globalThis.fetch).toHaveBeenCalledTimes(25);
  });

  it('stops early when a page comes back empty', async () => {
    stubFetchSequence([
      makePage(2000, 2500, 0),
      { transactions: [], total_count: 2500, limit: 2000, offset: 2000 },
    ]);

    const result = await fetchAllTransactions();

    expect(result.transactions).toHaveLength(2000);
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it('carries filter options on every page request', async () => {
    stubFetchSequence([makePage(2, 2, 0)]);

    await fetchAllTransactions(undefined, {
      account: 'acc1',
      categoryId: 'food',
      month: '2026-01'
    });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions?limit=2000&offset=0&account=acc1&category_id=food&month=2026-01');
  });
});

describe('fetchCategoryMonthTransactions', () => {
  it('passes route filters through as paginated query parameters', async () => {
    stubFetchSequence([makePage(2, 2, 0)]);

    const result = await fetchCategoryMonthTransactions({
      resultId: 'r1',
      accountId: 'acc1',
      categoryId: 'food',
      monthId: '2026-01'
    });

    expect(result.transactions).toHaveLength(2);
    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).toBe('/api/v2/transactions?result_id=r1&limit=2000&offset=0&account=acc1&category_id=food&month=2026-01');
  });

  it('omits result_id from the request when the route has none', async () => {
    stubFetchSequence([makePage(0, 0, 0)]);

    await fetchCategoryMonthTransactions({
      resultId: null,
      accountId: 'acc1',
      categoryId: 'food',
      monthId: '2026-01'
    });

    const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
    expect(url).not.toContain('result_id');
  });
});

describe('updateTransaction', () => {
  it('sends a PUT request with the correction payload', async () => {
    const updated = { id: 5, partner: 'Renamed Store' };
    stubFetch(updated);

    const result = await updateTransaction(5, { partner: 'Renamed Store' });

    expect(result).toEqual(updated);
    const [url, init] = vi.mocked(globalThis.fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/v2/transactions/5');
    expect(init.method).toBe('PUT');
    expect(init.body).toBe(JSON.stringify({ partner: 'Renamed Store' }));
  });

  it('serializes a null category so the category can be cleared', async () => {
    stubFetch({ id: 5, category_id: null });

    await updateTransaction(5, { category_id: null });

    const init = (vi.mocked(globalThis.fetch).mock.calls[0] as [string, RequestInit])[1];
    expect(init.body).toBe(JSON.stringify({ category_id: null }));
  });

  it('throws when the update is rejected', async () => {
    stubFetch({ error: 'Transaction not found' }, false);

    await expect(updateTransaction(999, { notice: 'x' })).rejects.toThrow('Transaction not found');
  });
});
