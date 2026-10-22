/**
 * Unit tests for the account/category/month result transform
 * @module test/resultsTransform
 */

import { describe, it, expect } from 'vitest';
import { transformToResultsApiResponse } from '../src/js/resultsTransform';
import type { TransactionListItem } from '../src/types/api';

/**
 * Minimal transaction fixture
 */
function makeTransaction(overrides: Partial<TransactionListItem>): TransactionListItem {
  return {
    id: 1,
    account: 'a1',
    category_id: 'grocery',
    date: '2025-01-15',
    amount: 100,
    currency: 'HUF',
    original_partner: 'Store',
    partner: null,
    original_notice: null,
    notice: null,
    confidence: null,
    transaction_type: 'type',
    ...overrides
  } as TransactionListItem;
}

describe('transformToResultsApiResponse', () => {
  it('groups transactions by account, category, and month', () => {
    const result = transformToResultsApiResponse([
      makeTransaction({ id: 1, account: 'a1', category_id: 'grocery', date: '2025-01-15', amount: 100 }),
      makeTransaction({ id: 2, account: 'a1', category_id: 'grocery', date: '2025-01-20', amount: 50 }),
      makeTransaction({ id: 3, account: 'a1', category_id: 'fee', date: '2025-02-01', amount: 10 }),
      makeTransaction({ id: 4, account: 'a2', category_id: 'grocery', date: '2025-01-05', amount: 5 })
    ]);

    expect(result.accounts).toHaveLength(2);

    const a1 = result.accounts.find(a => a.id === 'a1');
    expect(a1).toBeDefined();
    expect(a1?.data).toHaveLength(2);

    const groceryJanuary = a1?.data?.find(row => row.category_id === 'grocery' && row.date === '2025-01');
    expect(groceryJanuary?.total.raw).toBe(150);
    expect(groceryJanuary?.total.display).toBe('150.00');
    expect(groceryJanuary?.details).toHaveLength(2);
    expect(groceryJanuary?.is_calculated).toBe(false);

    const a2 = result.accounts.find(a => a.id === 'a2');
    expect(a2?.data).toHaveLength(1);
  });

  it('uses the first transaction currency as the account currency', () => {
    const result = transformToResultsApiResponse([
      makeTransaction({ account: 'a1', currency: 'EUR' })
    ]);
    expect(result.accounts[0]?.currency).toBe('EUR');
  });

  it('skips groups whose month key cannot be parsed', () => {
    const result = transformToResultsApiResponse([
      makeTransaction({ date: 'not-a-date' })
    ]);
    expect(result.accounts[0]?.data).toHaveLength(0);
  });

  it('falls back to uncategorized for missing category ids', () => {
    const result = transformToResultsApiResponse([
      makeTransaction({ category_id: null as unknown as string })
    ]);
    expect(result.accounts[0]?.data?.[0]?.category_id).toBe('uncategorized');
  });

  it('carries an empty highlights map', () => {
    const result = transformToResultsApiResponse([]);
    expect(result.accounts).toHaveLength(0);
    expect(result.highlights).toEqual({});
  });
});
