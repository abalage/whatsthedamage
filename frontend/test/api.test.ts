/**
 * Unit tests for API layer optional result_id handling
 * @module test/api
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  fetchTransactionsByResult,
  fetchAggregatedTransactions,
  fetchProcessingResultMetadata,
} from '../src/js/api.js';

const stubFetch = (data: unknown, ok = true): void => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok,
    status: ok ? 200 : 400,
    statusText: ok ? 'OK' : 'Bad Request',
    json: async () => data,
  } as Response)));
};

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
});
